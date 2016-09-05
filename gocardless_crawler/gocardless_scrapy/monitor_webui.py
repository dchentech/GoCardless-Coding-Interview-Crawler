# -*-coding:utf-8-*-

import cherrypy


class MonitorWebui(object):

    def __init__(self, master):
        self.master = master

    @cherrypy.expose
    def index(self):
        return self.master.status().replace("\n", "<br/>")
