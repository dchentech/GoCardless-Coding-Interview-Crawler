# -*-coding:utf-8-*-

from parsel import Selector
import urllib2
from six.moves.urllib.parse import urljoin as _urljoin
from urlparse import urlparse


class Request(object):

    def __init__(self, url, func=None, callback=lambda: None):
        self.url = url
        self.func = func
        self.callback = callback

        response = urllib2.urlopen(self.url)
        self.html = unicode(response.read(), "utf-8")

    def __repr__(self):
        return "Request<url:" + self.url + ">"

    def css(self, query):
        dom = Selector(text=(self.html))
        return dom.css(query)

    def urljoin(self, path):
        # http://stackoverflow.com/questions/9626535/get-domain-name-from-url
        parsed_uri = urlparse(self.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return _urljoin(domain, path)
