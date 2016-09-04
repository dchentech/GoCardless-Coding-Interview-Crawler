# -*-coding:utf-8-*-

import os
from .spider import Spider
from .http_request import Request
from Queue import Queue
import threading
import time

class scrapy(object):
    Spider = Spider
    thread_count = 10
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

        self.crawler = self.crawler_recipe()

    def process(self):
        self.start_worker_threads()
        self.fetch_init_urls()
        self.check_if_job_is_done()

    def fetch_init_urls(self):
        for url in self.crawler.start_urls:
            self.job_queue.put(Request(url, self.crawler.parse))
        for request in self.crawler.start_requests():
            self.job_queue.put(request)
        assert self.job_queue.qsize() != 0
        # job_queue.join()  # block until all tasks are done

    def check_if_job_is_done(self):
        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)
            # If we process the last item, then exit.
            if self.job_queue.empty():
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

    def start_worker_threads(self):
        print "2. Create %s threads ..." % self.thread_count
        for idx in xrange(self.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.worker_func(),
                                 args=(self.job_queue,
                                       self.crawler,
                                       self.output))
            t.start()

# TODO dead link
    def worker_func(self):
        def worker(q, crawler, output):
            print "[thread %s] starts ..." % threading.current_thread().name

            while True:
                time.sleep(scrapy.thread_sleep_seconds)
                if not q.empty():
                    item = q.get()
                    if item is not None:
                        print "processing item: ", item
                        try:
                            for item2 in crawler.parse(item):
                                if isinstance(item2, Request):
                                    q.put(item2)
                                else:
                                    output.put(item2)
                            q.task_done()
                        except:
                            raise
                            os._exit(-1)

                    print "Current queue size is %s ..." % \
                          q.qsize()
        return worker

__all__ = ['scrapy', 'Request']
