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
from .models import LinkItem, ErrorLog
from .monitor_webui import MonitorWebui


class scrapy(object):
    Spider = Spider

    # One cpu, 10 threads = 30%, 20 threads = 107%
    thread_count = 50

    thread_sleep_seconds = 10 * 0.001
    thread_check_queue_finished_seconds = 3
    thread_sync_db_wait_seconds = 5
    thread_sync_db_max_records_one_time = 100

    db_name = "gocardless"

    @classmethod
    def run(cls, crawler_recipe):
        print "... begin to run ", crawler_recipe
        crawler = cls(crawler_recipe)
        crawler.work()

    def __init__(self, crawler_recipe):
        self.crawler_recipe = crawler_recipe

        # TODO insert errors into db

        # NOTE all below BlockingQueue would be lost, if you kill the process.

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
        self.links_done = LinkItem.links_done()

        self.resume_unfinished_requests()
        self.start_crawler_worker_threads()
        self.sync_db_worker_thread = self.start_sync_db_worker_thread()
        self.fetch_init_links()
        self.start_monitor_webui()
        self.check_if_job_is_done()

    def put_again(self, request):
        self.put(request, force=True)

    def put(self, request, force=False):
        """ Remove duplicated request.  """
        is_done = request.url in self.links_done
        if (not force) and (not is_done):
            # Ignore other domain urls
            if Request.is_gocardless(request):
                self.requests_todo.put(request)
                self.links_done.add(request.url)
        else:
            if self.debug:
                print request.url + " is already in the queue, and maybe " \
                                    "processed."

    def fetch_init_links(self):
        for url in self.crawler.start_urls:
            # always put start_urls
            self.put_again(Request(url, self.crawler.parse))
        for request in self.crawler.start_requests():
            self.put(request)
        assert self.requests_todo.qsize() > 0

    def resume_unfinished_requests(self):
        for link in LinkItem.links_todo():
            self.put(Request(link, self.crawler.parse))

    def check_if_job_is_done(self):
        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)

            print self

            # If we process the last item, then exit.
            if self.requests_todo.empty() and self.link_items_output.empty():
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
        return t

    def sync_db_worker_func(self):
        def worker(master):
            thread_info = "[thread sync_db_worker %s] " % \
                          threading.current_thread().name
            print thread_info + "starts ..."

            while True:
                time.sleep(scrapy.thread_sync_db_wait_seconds)

                sync_count = 0
                print thread_info + "begin sync ..."
                while not master.link_items_output.empty():
                    link_item_json = master.link_items_output.get()
                    if link_item_json is not None:
                        LinkItem.insert_item(link_item_json["link"],
                                             link_item_json["assets"])
                        sync_count += 1
                        if (sync_count >
                                self.thread_sync_db_max_records_one_time):
                            break
                msg = "synced %s records at this time ..." % (sync_count,)
                print thread_info + msg

                while not master.errors.empty():
                    error_json = master.errors.get()
                    if error_json is not None:
                        ErrorLog.insert_item(error_json["link"],
                                             error_json["error"])

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
            self.put(item2)
        else:
            self.link_items_output.put(item2)

    def __repr__(self):
        return "\n\n==============================\n" \
               "requests_todo size: %s\n" \
               "link_items_output size: %s\n" \
               "error size: %s\n" \
               "threads count:  %s\n"  \
               "table count:  %s\n" % \
               (self.requests_todo.qsize(),
                self.link_items_output.qsize(),
                ErrorLog.select().count(),
                threading.active_count(),
                LinkItem.select().count(),)

    def process(self, item):
        print "processing item: ", item
        try:
            for item2 in self.crawler.parse(item):
                self.continue_or_drop_item(item2)
        except (HTTPError, BadStatusLine, ) as e1:
            msg = (item, e1,)
            self.errors.put({"link": item.url, "error": msg})
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


__all__ = ['scrapy']
