# -*-coding:utf-8-*-

import os
import sys
import copy
from Queue import Queue
import threading
from multiprocessing import RawValue, Lock
import time
from urllib2 import HTTPError, URLError
import socket
import cherrypy
from .spider import Spider
from .http_request import Request

# TODO maybe use external memcached service
global url_added_mark
url_added_mark = dict()


class scrapy(object):
    Spider = Spider

    # One cpu, 10 threads = 30%, 20 threads = 107%
    # thread_count = 20
    thread_count = 99

    thread_sleep_seconds = 10 * 0.001
    thread_check_queue_finished_seconds = 3

    @classmethod
    def run(cls, crawler_recipe):
        print "... begin to run ", crawler_recipe
        crawler = cls(crawler_recipe)
        crawler.process()

    def __init__(self, crawler_recipe):
        self.crawler_recipe = crawler_recipe

        # https://docs.python.org/2/library/queue.html
        # TODO maybe optimize maxsize
        self.job_queue = Queue()  # It's thread-safe
        self.output = Queue()
        self.errors = Queue()

        self.crawler = self.crawler_recipe()

        self.debug = False

        self.urls_total_counter = Counter(0)
        self.assets_in_every_url_total_counter = Counter(0)

    def process(self):
        self.start_worker_threads()
        self.fetch_init_urls()
        self.start_monitor_webui()
        self.check_if_job_is_done()

        print "output: %s" % self.output
        print "errors: %s" % self.errors

    def put_again(self, request):
        self.put(request, force=True)

    def put(self, request, force=False):
        """ Remove duplicated request.  """
        if (not force) and (request.url not in url_added_mark):
            self.job_queue.put(request)
            url_added_mark[request.url] = True
            self.urls_total_counter.increment()
        else:
            if self.debug:
                print request.url + " is already in the queue, and maybe " \
                                    "processed."

    def fetch_init_urls(self):
        for url in self.crawler.start_urls:
            self.put(Request(url, self.crawler.parse))
        for request in self.crawler.start_requests():
            self.put(request)
        assert self.job_queue.qsize() != 0
        # job_queue.join()  # block until all tasks are done

    def check_if_job_is_done(self):
        previous_queue_count = 0

        while True:
            previous_queue_count = self.job_queue.qsize()

            time.sleep(scrapy.thread_check_queue_finished_seconds)

            print self

            # If we process the last item, then exit.
            if self.job_queue.empty():
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

            if previous_queue_count == self.job_queue.qsize():
                # NOTE to find out why not peak the queue
                print "current queue: %s" % self.inspect_queue(self.job_queue)

    def inspect_queue(self, q1):
        try:
            q2 = copy.deepcopy(q1)
        except TypeError as e:
            return str(e)

        l2 = list()
        while not q2.empty():
            l2.append(q2.get())
        return "queue:%s: %s" % (q1, l2)

    def start_worker_threads(self):
        print "Create %s threads ..." % self.thread_count
        for idx in xrange(self.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.worker_func(),
                                 args=(self, ))
            t.start()

    def continue_or_drop_item(self, item2):
        if isinstance(item2, Request):
            # Ignore other domain urls
            if Request.is_gocardless(item2):
                self.put(item2)
        else:
            self.assets_in_every_url_total_counter.increment()
            self.output.put(item2)

    def __repr__(self):
        return "\n\n==============================\n" \
               "Current queue size: %s\n" \
               "output size: %s\n" \
               "error size: %s\n" \
               "threads count:  %s\n"  \
               "urls_total_counter: %s\n" \
               "assets_in_every_url_total_counter: %s\n" % \
               (self.job_queue.qsize(),
                self.output.qsize(),
                self.errors.qsize(),
                threading.active_count(),
                self.urls_total_counter,
                self.assets_in_every_url_total_counter)

    def __repr_detail__(self):
        return "\n\n==============================\n" \
               "queue: %s\n" \
               "output: %s\n" \
               "error: %s\n" \
               "threads count:  %s\n"  \
               "urls_total_counter: %s\n" \
               "assets_in_every_url_total_counter: %s\n" % \
               (self.inspect_queue(self.job_queue),
                self.inspect_queue(self.output),
                self.inspect_queue(self.errors),
                threading.active_count(),
                self.urls_total_counter,
                self.assets_in_every_url_total_counter)

    def worker_func(self):
        def worker(master):
            thread_info = "[thread %s] " % threading.current_thread().name
            print thread_info + "starts ..."

            while True:
                time.sleep(scrapy.thread_sleep_seconds)

                if not master.job_queue.empty():
                    item = master.job_queue.get()
                    if item is not None:
                        print "processing item: ", item
                        try:
                            for item2 in master.crawler.parse(item):
                                master.continue_or_drop_item(item2)
                            master.job_queue.task_done()
                        except (HTTPError, ) as e1:
                            msg = (item, e1,)
                            master.errors.put(msg)
                        except (socket.timeout, socket.error, URLError, ) \
                                as e1:
                            # NOTE URLError is alos timeout error.
                            master.put_again(item)
                        except:
                            print "Unexpected error:", sys.exc_info()[0]
                            raise
        return worker

    def start_monitor_webui(self):
        def webui(self):
            cherrypy.quickstart(MonitorWebui(self), "/")
        threading.Thread(target=webui, args=(self, )).start()


# http://stackoverflow.com/questions/35088139/how-to-make-a-thread-safe-global-counter-in-python
class Counter(object):
    def __init__(self, value=0):
        # RawValue because we don't need it to create a Lock:
        self.val = RawValue('i', value)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def value(self):
        with self.lock:
            return self.val.value

    def __repr__(self):
        return str(self.val)


class MonitorWebui(object):

    def __init__(self, master):
        self.master = master

    @cherrypy.expose
    def index(self):
        return self.master.__repr_detail__().replace("\n", "<br/>")


__all__ = ['scrapy', 'Request']
