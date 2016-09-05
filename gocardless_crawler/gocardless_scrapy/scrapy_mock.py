# -*-coding:utf-8-*-

import os
import sys
# https://docs.python.org/2/library/queue.html
# Queue is thread-safe
from Queue import Queue as BlockingQueue
import threading
import time
from urllib2 import HTTPError, URLError
from httplib import BadStatusLine
import socket
from peewee import IntegrityError, OperationalError
from .http_request import Request
from .models import LinkItem
from .scrapy_status import ScrapyStatus
from .scrapy_threads import ScrapyThreads
from .conf import thread_check_queue_finished_seconds

global crawler_thread_to_link_map
crawler_thread_to_link_map = dict()


class scrapy(ScrapyStatus, ScrapyThreads):
    """
    A mini mock scrapy framework.
    """
    class Spider:
        """
        I'm a fake mock class
        """

    crawler_thread_to_link_map = crawler_thread_to_link_map

    @classmethod
    def run(cls, crawler_recipe):
        """
        The public API.

        e.g. scrapy.run(GoCardlessWebsiteCrawler)
        """
        print "... begin to run ", crawler_recipe
        crawler = cls(crawler_recipe)
        crawler.work()

    def __init__(self, crawler_recipe):
        self.crawler_recipe = crawler_recipe

        # NOTE all below BlockingQueue would be lost, if you kill the process.

        # Inserted from database and crawler workers
        self.requests_todo = BlockingQueue()

        # Inserted from crawler workers, and would be readed by
        # Insert-database-thread
        self.link_items_output = BlockingQueue()

        self.errors = BlockingQueue()

        self.crawler = self.crawler_recipe()

        self.debug = False

    def work(self):
        """
        The main function.
        """
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
            # always put start_urls every time
            self.put_again(Request(url, self.crawler.parse))
        for request in self.crawler.start_requests():
            self.put(request)
        assert self.requests_todo.qsize() > 0

    def resume_unfinished_requests(self):
        for link in LinkItem.links_todo():
            self.put(Request(link, self.crawler.parse))

    def check_if_job_is_done(self):
        while True:
            time.sleep(thread_check_queue_finished_seconds)

            print self

            # If we process the last item, then exit.
            if self.requests_todo.empty() and self.link_items_output.empty() \
                    and (self.workings_ids_count == 0):
                # TODO check all crawler threads are idle.
                print "[thread %s] exits ..." % threading.current_thread().name
                os._exit(0)

    def continue_or_drop_item(self, item2):
        if isinstance(item2, Request):
            self.put(item2)
        else:
            self.link_items_output.put(item2)

    def __repr__(self):
        return self.process_status

    def process(self, item):
        print "processing item: ", item
        try:
            for item2 in self.crawler.parse(item):
                self.continue_or_drop_item(item2)
        except (HTTPError, BadStatusLine, ) as e1:
            self.errors.put({"link": item.url, "error": str(e1)})
        except (socket.timeout, socket.error, URLError, ):
            # NOTE URLError is alos timeout error.
            self.put_again(item)
        except (IntegrityError, OperationalError):
            # TODO should remove it, crawlers don't write to db directly now,
            # they write data to Queue.
            pass  # ignore peewee errors
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print """
It shouldn't happen, please report this issue to developers.
And they would fix it.
            """
            raise


__all__ = ['scrapy']
