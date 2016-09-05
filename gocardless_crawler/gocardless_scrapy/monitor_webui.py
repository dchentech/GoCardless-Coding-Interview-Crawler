# -*-coding:utf-8-*-

import cherrypy


class MonitorWebui(object):

    def __init__(self, master):
        self.master = master

    @cherrypy.expose
    def index(self):
        content = self.status().replace("\n", "<br/>")
        return content

    def status(self):
        def join_lines(lines):
            return "\n" + "\n".join(lines)

        return "==== memory status" + \
               join_lines(self.master.memory_status) + \
               "\n\n\n" + \
               "==== database status" + \
               join_lines(self.master.database_status) + \
               "\n\n\n" + \
               "==== threads status" + \
               join_lines(self.master.threads_status) + \
               "\n\n\n" + \
               "==== Table[LinkItem] recent records" + \
               join_lines(self.master.table_LinkItem_lastest_records) + \
               "\n\n\n" + \
               "==== Table[ErrorLog] recent records" + \
               join_lines(self.master.table_ErrorLog_lastest_records)
