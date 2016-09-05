# -*-coding:utf-8-*-

import os
import sys
import copy
from Queue import Queue
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
from .models import UrlItem, UrlAssets, PeeweeUtils

# TODO maybe use external memcached service
global url_added_mark
url_added_mark = dict()


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

        # https://docs.python.org/2/library/queue.html
        # TODO maybe optimize maxsize
        # It's thread-safe
        self.errors = Queue()

        self.crawler = self.crawler_recipe()

        self.debug = False

    def work(self):
        UrlItem.init_db_and_table("mysql", self.db_name)
        UrlAssets.init_db_and_table("mysql", self.db_name)

        self.urls_total_counter = Counter(UrlItem.finished_urls_count())

        for processed_url in UrlItem.finished_urls():
            url_added_mark[processed_url] = True

        self.start_worker_threads()
        self.fetch_init_urls()
        self.start_monitor_webui()
        self.check_if_job_is_done()

        print "errors: %s" % self.errors

    def put_again(self, request):
        self.put(request, force=True)

    def put(self, request, force=False):
        """ Remove duplicated request.  """
        if (not force) and (request.url not in url_added_mark):
            def func():
                UrlItem.create(**{"url": request.url})
            PeeweeUtils.catch_OperationalError(func)

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
        assert UrlItem.select().count() != 0

    def check_if_job_is_done(self):
        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)

            print self

            # If we process the last item, then exit.
            if UrlItem.is_empty():
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

    def start_worker_threads(self):
        print "Create %s threads ..." % self.thread_count
        for idx in xrange(self.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.worker_func(),
                                 args=(self, idx + 1, ))
            t.start()

    def continue_or_drop_item(self, item2):
        if isinstance(item2, Request):
            # Ignore other domain urls
            if Request.is_gocardless(item2):
                self.put(item2)
        else:
            UrlAssets.upsert(item2["url"], item2["assets"])

    def __repr__(self):
        return "\n\n==============================\n" \
               "Current queue size: %s\n" \
               "output size: %s\n" \
               "error size: %s\n" \
               "threads count:  %s\n"  \
               "urls_total_counter: %s\n" % \
               (UrlItem.unfinished_count(),
                UrlAssets.total_count(),
                self.errors.qsize(),
                threading.active_count(),
                self.urls_total_counter,)

    def status(self):
        return "\n\n==============================\n" \
               "queue: %s\n" \
               "output: %s\n" \
               "error: %s\n" \
               "threads count:  %s\n"  \
               "urls_total_counter: %s\n" % \
               (UrlItem.read_all(),
                UrlAssets.read_all(),
                self.inspect_queue(self.errors),
                threading.active_count(),
                self.urls_total_counter,)

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
            # ignore peewee errors
            pass
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def worker_func(self):
        def worker(master, wait_seconds):
            thread_info = "[thread %s] " % threading.current_thread().name
            print thread_info + "starts ..."

            # NOTE avoid sqlite db lock at init time.
            time.sleep(wait_seconds)

            while True:
                time.sleep(scrapy.thread_sleep_seconds)

                url_item = None
                if not UrlItem.is_empty():
                    try:
                        url_item = UrlItem.get()
                    except OperationalError:
                        pass

                if url_item is not None:
                    item = Request(url_item.url)
                    master.process(item)

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


__all__ = ['scrapy', 'Request', 'UrlItem']
