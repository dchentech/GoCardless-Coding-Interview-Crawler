# -*-coding:utf-8-*-

from parsel import Selector
import urllib2
import pycurl
from StringIO import StringIO
from six.moves.urllib.parse import urljoin as _urljoin
from urlparse import urlparse


class Request(object):

    def __init__(self, url, func=None, callback=lambda: None):
        self.url = url.rstrip("/")
        self.url = self.url.split("#")[0]  # remove hash part
        self.url = self.url.encode('ascii', 'ignore').decode('ascii')

        self.func = func
        self.callback = callback

        self.network_method = [read_via_pycurl, read_via_urllib2][0]

    def read_html(self):
        content = self.network_method(self.url)
        self.html = content.decode('utf-8', 'ignore')

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


def read_via_urllib2(url):
    return urllib2.urlopen(url).read()

def read_via_pycurl(url):
    """ http://pycurl.io/docs/latest/quickstart.html """
    _buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, _buffer)
    c.perform()
    c.close()

    body = _buffer.getvalue()
    # Body is a string in some encoding.
    # In Python 2, we can print it without knowing what the encoding is.
    return body
