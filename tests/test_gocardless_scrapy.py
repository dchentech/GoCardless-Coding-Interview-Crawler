# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler.gocardless_scrapy.http_request import Request


class TestGoCardlessScrapy(unittest.TestCase):

    def test_request(self):
        response = Request("https://gocardless.com/", lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())

    def test_invalid_html(self):
        """
        Fix self.html = unicode(response.read(), "utf-8")
        UnicodeDecodeError: 'utf8' codec can't decode byte 0xc3 in position 588: invalid continuation byte
        """
        url = "https://gocardless.com/fr-be"
        response = Request(url, lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())
