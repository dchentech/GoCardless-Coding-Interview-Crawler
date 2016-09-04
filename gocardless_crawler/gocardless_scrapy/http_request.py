# -*-coding:utf-8-*-

class Request(object):

    def __init__(self, url, func):
        self.url = url
        self.func = func
        print "get url: ", url

    def __repr__(self):
        return "Request<url:" + self.url + ">"
