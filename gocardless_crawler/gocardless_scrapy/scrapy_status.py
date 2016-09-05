# -*-coding:utf-8-*-

import cgi
import json
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
        info = self.crawler_worker_threads_status()
        return [
            "sync_db_worker_thread.isAlive(): " +
            str(self.master.sync_db_worker_thread.isAlive()),
            "Crawler threads info " + str(info) + "\n",
        ]

    @property
    def table_LinkItem_lastest_records(self):
        return select_lastest_records(LinkItem)

    @property
    def table_ErrorLog_lastest_records(self):
        return select_lastest_records(ErrorLog)

    @property
    def all_status(self):
        working_info = self.workings_items
        return "==== working items[" + str(len(working_info)) + "]\n" + \
            json.dumps(working_info) + \
            "\n\n\n" + \
            self.process_status + \
            "\n\n\n" + \
            "==== Table[LinkItem] recent records" + \
            join_lines(self.master.table_LinkItem_lastest_records) + \
            "\n\n\n" + \
            "==== Table[ErrorLog] recent records" + \
            join_lines(self.master.table_ErrorLog_lastest_records)

    @property
    def process_status(self):
        return "==== memory status" + \
               join_lines(self.master.memory_status) + \
               "\n\n\n" + \
               "==== database status" + \
               join_lines(self.master.database_status) + \
               "\n\n\n" + \
               "==== threads status" + \
               join_lines(self.master.threads_status)


def select_lastest_records(model):
    records = list(model.select().order_by(model.id.desc()).limit(10))
    return [cgi.escape(repr(i)) + "\n" for i in records]

def join_lines(lines):
    return "\n" + "\n".join(lines)

__all__ = ['ScrapyStatus']
