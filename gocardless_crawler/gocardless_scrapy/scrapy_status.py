# -*-coding:utf-8-*-

import threading
import cgi
from .models import LinkItem, ErrorLog


class ScrapyStatus():

    @property
    def master(self):
        """ make an alias """
        return self

    @property
    def memory_status(self):
        return [
            "requests_todo.size: " + str(self.master.requests_todo.qsize()),
            "errors.size: " + str(self.master.errors.qsize()),
        ]

    @property
    def database_status(self):
        return [
            "LinkItem.count: " + str(LinkItem.select().count()),
            "ErrorLog.count: " + str(ErrorLog.select().count()),
        ]

    @property
    def threads_status(self):
        return [
            "sync_db_worker_thread.isAlive(): " +
            str(self.master.sync_db_worker_thread.isAlive()),
            "threads count:  " + str(threading.active_count()),
        ]

    @property
    def table_LinkItem_lastest_records(self):
        return select_lastest_records(LinkItem)

    @property
    def table_ErrorLog_lastest_records(self):
        return select_lastest_records(ErrorLog)

def select_lastest_records(model):
    records = list(model.select().order_by(model.id.desc()).limit(10))
    return [cgi.escape(repr(i)) + "\n" for i in records]


__all__ = ['ScrapyStatus']
