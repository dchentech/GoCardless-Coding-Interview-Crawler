# -*-coding:utf-8-*-

from .spider import Spider
from .http_request import Request

class scrapy(object):
    Spider = Spider
    hello = "world"

__all__ = ['scrapy', 'Request']
