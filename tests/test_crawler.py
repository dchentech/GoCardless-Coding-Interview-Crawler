# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler import GoCardlessWebsiteCrawler


class TestCrawler(unittest.TestCase):

    def test_sitemap_urls(self):
        urls = GoCardlessWebsiteCrawler().sitemap_urls
        self.assertTrue(len(urls) > 0)
        self.assertTrue("gocardless.com" in urls[0])
