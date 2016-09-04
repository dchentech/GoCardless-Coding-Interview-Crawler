# -*-coding:utf-8-*-

import os
import sys
from .spider import Spider
from .http_request import Request
from Queue import Queue
import threading
import time
from urllib2 import HTTPError
import socket

# TODO maybe use external memcached service
global url_processed_mark
url_processed_mark = dict()


class scrapy(object):
    Spider = Spider

    # One cpu, 10 threads = 30%, 20 threads = 107%
    # thread_count = 20
    thread_count = 40

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

    def process(self):
        self.start_worker_threads()
        self.fetch_init_urls()
        self.check_if_job_is_done()

        print "output: %s" % self.output
        print "errors: %s" % self.errors

    def put_again(self, request):
        self.put(request, force=True)

    def put(self, request, force=False):
        """ Remove duplicated request.  """
        if (not force) and (request.url not in url_processed_mark):
            self.job_queue.put(request)
            url_processed_mark[request.url] = True
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
        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)

            print "master: %s" % self

            # If we process the last item, then exit.
            if self.job_queue.empty():
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

    def start_worker_threads(self):
        print "Create %s threads ..." % self.thread_count
        for idx in xrange(self.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.worker_func(),
                                 args=(self, ))
            t.start()

    def continue_or_drop_item(self, item2):
        if isinstance(item2, Request):
            if Request.is_gocardless(item2):
                self.put(item2)
        else:
            self.output.put(item2)

    def __repr__(self):
        return "Current queue size is %s. " \
               "And output size is %s, and error size is %s. " \
               "And threads count is %s.\n" % \
               (self.job_queue.qsize(),
                self.output.qsize(), self.errors.qsize(),
                threading.active_count())

    def worker_func(self):
        def worker(master):
            print "[thread %s] starts ..." % threading.current_thread().name

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
                        except (socket.timeout, ) as e1:
                            master.put_again(item)
                        except:
                            sys.exit()
        return worker

__all__ = ['scrapy', 'Request']
