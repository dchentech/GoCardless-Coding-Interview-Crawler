# -*-coding:utf-8-*-

from .spider import Spider
from .http_request import Request

class scrapy(object):
    Spider = Spider

__all__ = ['scrapy', 'Request']
