# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler.gocardless_scrapy.http_request import Request


class TestRequest(unittest.TestCase):

    def test_css(self):
        response = Request("https://gocardless.com/", lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())
