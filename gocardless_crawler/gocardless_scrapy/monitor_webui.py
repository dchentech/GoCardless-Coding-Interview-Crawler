# -*-coding:utf-8-*-

import cherrypy


class MonitorWebui(object):

    def __init__(self, master):
        self.master = master

    @cherrypy.expose
    def index(self):
        content = self.master.all_status.replace("\n", "<br/>")
        return content
