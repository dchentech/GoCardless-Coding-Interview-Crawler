# -*-coding:utf-8-*-

from parsel import Selector
import urllib2
from six.moves.urllib.parse import urljoin as _urljoin
from urlparse import urlparse
import codecs


class Request(object):

    def __init__(self, url, func=None, callback=lambda: None):
        self.url = url.rstrip("/")
        self.url = self.url.split("#")[0]  # remove hash part
        self.url = self.url.encode('ascii', 'ignore').decode('ascii')

        self.func = func
        self.callback = callback

    def read_html(self):
        content = urllib2.urlopen(self.url).read()
        self.html = unicode(content.strip(codecs.BOM_UTF8), 'utf-8')

    def __repr__(self):
        return "Request<url: \"" + self.url + "\">"

    def css(self, query):
        self.read_html()
        dom = Selector(text=(self.html))
        return dom.css(query)

    def urljoin(self, path):
        # http://stackoverflow.com/questions/9626535/get-domain-name-from-url
        parsed_uri = urlparse(self.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return _urljoin(domain, path)

    @classmethod
    def is_gocardless(cls, request):
        parsed_uri = urlparse(request.url)
        return "gocardless" in parsed_uri.netloc.lower()
