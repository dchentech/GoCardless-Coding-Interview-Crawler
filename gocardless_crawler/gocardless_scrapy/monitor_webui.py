# -*-coding:utf-8-*-

import cherrypy
import threading
from .models import LinkItem, ErrorLog


class MonitorWebui(object):

    def __init__(self, master):
        self.master = master

    @cherrypy.expose
    def index(self):
        return self.status().replace("\n", "<br/>")

    def status(self):
        def join_lines(lines):
            return "\n" + "\n".join(lines)

        memory_status = [
            "requests_todo.size: " + str(self.master.requests_todo.qsize()),
            "errors.size: " + str(self.master.errors.qsize()),
        ]

        database_status = [
            "LinkItem.count: " + str(LinkItem.select().count()),
            "ErrorLog.count: " + str(ErrorLog.select().count()),
        ]

        threads_status = [
            "sync_db_worker_thread.isAlive(): " +
            str(self.master.sync_db_worker_thread.isAlive()),
            "threads count:  " + str(threading.active_count()),
        ]

        def select_lastest_records(model):
            records = list(model.select().order_by(model.id.desc()).limit(10))
            return [str(i) for i in records]
        table_LinkItem_lastest_records = select_lastest_records(LinkItem)
        table_ErrorLog_lastest_records = select_lastest_records(ErrorLog)

        return "==== memory status" + \
               join_lines(memory_status) + \
               "\n\n\n" + \
               "==== database status" + \
               join_lines(database_status) + \
               "\n\n\n" + \
               "==== threads status" + \
               join_lines(threads_status) + \
               "\n\n\n" + \
               "==== Table[LinkItem] recent records" + \
               join_lines(table_LinkItem_lastest_records) + \
               "\n\n\n" + \
               "==== Table[ErrorLog] recent records" + \
               join_lines(table_ErrorLog_lastest_records)
