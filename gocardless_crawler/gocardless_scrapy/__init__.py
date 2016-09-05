# -*-coding:utf-8-*-

import os
import sys
import copy
# https://docs.python.org/2/library/queue.html
# Queue is thread-safe
from Queue import Queue as BlockingQueue
import threading
from multiprocessing import RawValue, Lock
import time
from urllib2 import HTTPError, URLError
from httplib import BadStatusLine
import socket
import cherrypy
from peewee import IntegrityError, OperationalError
from .spider import Spider
from .http_request import Request
from .models import LinkItem


class scrapy(object):
    Spider = Spider

    # One cpu, 10 threads = 30%, 20 threads = 107%
    thread_count = 50

    thread_sleep_seconds = 10 * 0.001
    thread_check_queue_finished_seconds = 3

    db_name = "gocardless"

    @classmethod
    def run(cls, crawler_recipe):
        print "... begin to run ", crawler_recipe
        crawler = cls(crawler_recipe)
        crawler.work()

    def __init__(self, crawler_recipe):
        self.crawler_recipe = crawler_recipe

        # TODO change below two API
        # Inserted from database and crawler workers
        self.requests_todo = BlockingQueue()

        # Inserted from crawler workers, and would be readed by
        # Insert-database-thread
        self.link_items_output = BlockingQueue()

        self.errors = BlockingQueue()

        self.crawler = self.crawler_recipe()

        self.debug = False

    def work(self):
        LinkItem.load_previous_status()

        _links_total_counter = LinkItem.current_processed_links_count()
        self.links_total_counter = Counter(_links_total_counter)

        self.start_crawler_worker_threads()
        self.start_sync_db_worker_thread()
        self.fetch_init_links()
        self.start_monitor_webui()
        self.check_if_job_is_done()

        print "errors: %s" % self.errors

    def put_again(self, request):
        self.put(request, force=True)

    def put(self, request, force=False):
        """ Remove duplicated request.  """
        is_done = LinkItem.is_link_processed(request.url)
        if (not force) and (not is_done):
            self.requests_todo.put(request.url)
            self.links_total_counter.increment()
        else:
            if self.debug:
                print request.url + " is already in the queue, and maybe " \
                                    "processed."

    def fetch_init_links(self):
        for url in self.crawler.start_urls:
            self.put(Request(url, self.crawler.parse))
        for request in self.crawler.start_requests():
            self.put(request)
        assert self.requests_todo.qsize() > 0

    def check_if_job_is_done(self):
        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)

            print self

            # If we process the last item, then exit.
            if self.requests_todo.empty():
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

    def inspect_queue(self, q1):
        try:
            q2 = copy.deepcopy(q1)
        except TypeError as e:
            return str(e)

        l2 = list()
        while not q2.empty():
            l2.append(q2.get())
        return "queue:%s: %s" % (q1, l2)

    def start_sync_db_worker_thread(self):
        t = threading.Thread(target=self.sync_db_worker_func(),
                             args=(self, ))
        t.start()

    def sync_db_worker_func(self):
        def worker(master):
            thread_info = "[thread sync_db_worker %s] starts ..." % \
                          threading.current_thread().name
            print thread_info

            while True:
                time.sleep(scrapy.thread_sleep_seconds)

                if not master.link_items_output.empty():
                    link_item_json = master.link_items_output.get()
                    if link_item_json is not None:
                        LinkItem.insert_item(link_item_json["link"],
                                             link_item_json["assets"])

        return worker

    def start_crawler_worker_threads(self):
        print "Create %s threads ..." % self.thread_count
        for idx in xrange(self.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.crawler_worker_func(),
                                 args=(self, idx + 1, ))
            t.start()

    def continue_or_drop_item(self, item2):
        if isinstance(item2, Request):
            # Ignore other domain urls
            if Request.is_gocardless(item2):
                self.put(item2)

    def __repr__(self):
        return "\n\n==============================\n" \
               "Current queue size: %s\n" \
               "output size: %s\n" \
               "error size: %s\n" \
               "threads count:  %s\n"  \
               "links_total_counter: %s\n" % \
               (LinkItem.unfinished_count(),
                1,
                self.errors.qsize(),
                threading.active_count(),
                self.links_total_counter,)

    def status(self):
        return "\n\n==============================\n" \
               "queue: %s\n" \
               "output: %s\n" \
               "error: %s\n" \
               "threads count:  %s\n"  \
               "links_total_counter: %s\n" % \
               (LinkItem.read_all(),
                1,
                self.inspect_queue(self.errors),
                threading.active_count(),
                self.links_total_counter,)

    def process(self, item):
        print "processing item: ", item
        try:
            for item2 in self.crawler.parse(item):
                self.continue_or_drop_item(item2)
        except (HTTPError, BadStatusLine, ) as e1:
            msg = (item, e1,)
            self.errors.put(msg)
        except (socket.timeout, socket.error, URLError, ):
            # NOTE URLError is alos timeout error.
            self.put_again(item)
        except (IntegrityError, OperationalError):
            # TODO should remove it, crawlers don't write to db directly now,
            # they write data to Queue.
            pass  # ignore peewee errors
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def crawler_worker_func(self):
        def worker(master, wait_seconds):
            thread_info = "[thread %s] " % threading.current_thread().name
            print thread_info + "starts ..."

            # Don't start too fast.
            time.sleep(wait_seconds)

            while True:
                time.sleep(scrapy.thread_sleep_seconds)

                link_item = None
                if master.requests_todo.qsize() > 0:
                    link_item = master.requests_todo.get()
                    if link_item is not None:
                        master.process(link_item)

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
        return self.master.status().replace("\n", "<br/>")


__all__ = ['scrapy', 'Request', 'LinkItem']
