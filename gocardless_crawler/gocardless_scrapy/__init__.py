# -*-coding:utf-8-*-

import os
import sys
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

        instance = crawler_recipe()

        def worker(q):
            print "[thread %s] starts ..." % threading.current_thread().name

            while True:
                time.sleep(scrapy.thread_sleep_seconds)
                if not job_queue.empty():
                    item = job_queue.get()
                    print "item: ", item  # process item
                    job_queue.task_done()

                    print "Current job_queue.size is %s ..." % \
                          job_queue.qsize()

        # https://docs.python.org/2/library/queue.html
        # TODO maybe optimize maxsize
        print "1. Init job_queue ..."
        job_queue = Queue()  # It's thread-safe

        print "2. Create %s threads ..." % cls.thread_count
        for idx in xrange(cls.thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=worker, args=(job_queue,))
            t.start()

        print "3. Use a single thread to get all urls ..."
        for url in instance.start_urls:
            job_queue.put(Request(url, instance.parse))
        for request in instance.start_requests():
            job_queue.put(request)
        assert job_queue.qsize() != 0

        # job_queue.join()  # block until all tasks are done

        while True:
            time.sleep(scrapy.thread_check_queue_finished_seconds)
            # If we process the last item, then exit.
            if job_queue.empty():
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

# TODO dead link


__all__ = ['scrapy', 'Request']
