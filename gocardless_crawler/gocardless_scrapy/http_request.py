# -*-coding:utf-8-*-

from parsel import Selector
import urllib2


class Request(object):

    def __init__(self, url, func):
        self.url = url
        self.func = func

        response = urllib2.urlopen(self.url)
        self.html = unicode(response.read(), "utf-8")

    def __repr__(self):
        return "Request<url:" + self.url + ">"

    def css(self, query):
        dom = Selector(text=(self.html))
        return dom.css(query)
