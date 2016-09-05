# -*-coding:utf-8-*-

import threading
import time
import cherrypy
from .conf import thread_sleep_seconds, thread_sync_db_wait_seconds, \
    thread_sync_db_max_records_one_time, thread_count
from .models import LinkItem, ErrorLog
from .monitor_webui import MonitorWebui


class ScrapyThreads(object):

    def crawler_worker_func(self):
        def worker(master, wait_seconds):
            thread_info = "[thread %s] " % threading.current_thread().name
            print thread_info + "starts ..."

            # Don't start too fast.
            time.sleep(wait_seconds)

            while True:
                time.sleep(thread_sleep_seconds)

                link_item = None
                if master.requests_todo.qsize() > 0:
                    link_item = master.requests_todo.get()
                    if link_item is not None:
                        master.process(link_item)

        return worker

    def sync_db_worker_func(self):
        def worker(master):
            thread_info = "[thread sync_db_worker %s] " % \
                          threading.current_thread().name
            print thread_info + "starts ..."

            while True:
                time.sleep(thread_sync_db_wait_seconds)

                sync_count = 0
                print thread_info + "begin sync ..."
                while not master.link_items_output.empty():
                    link_item_json = master.link_items_output.get()
                    if link_item_json is not None:
                        LinkItem.insert_item(link_item_json["link"],
                                             link_item_json["assets"])
                        sync_count += 1
                        if (sync_count >
                                thread_sync_db_max_records_one_time):
                            break
                msg = "synced %s records at this time ..." % (sync_count,)
                print thread_info + msg

                while not master.errors.empty():
                    error_json = master.errors.get()
                    if error_json is not None:
                        ErrorLog.insert_item(error_json["link"],
                                             error_json["error"])

        return worker

    def start_monitor_webui(self):
        def webui(self):
            cherrypy.quickstart(MonitorWebui(self), "/")
        threading.Thread(target=webui, args=(self, )).start()

    def start_sync_db_worker_thread(self):
        t = threading.Thread(target=self.sync_db_worker_func(),
                             args=(self, ))
        t.start()
        return t

    def start_crawler_worker_threads(self):
        print "Create %s threads ..." % thread_count
        self.crawler_worker_threads = []
        for idx in xrange(thread_count):
            print "create thread[%s] ..." % (idx + 1)
            t = threading.Thread(target=self.crawler_worker_func(),
                                 args=(self, idx + 1, ))
            t.start()
            self.crawler_worker_threads.append(t)


__all__ = ['ScrapyThreads']
