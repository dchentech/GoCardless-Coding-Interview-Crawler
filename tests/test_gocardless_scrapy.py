# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler.gocardless_scrapy.http_request import Request
from gocardless_crawler.gocardless_scrapy.models import LinkItem


class TestGoCardlessScrapy(unittest.TestCase):

    test_url = "https://gocardless.com/"

    def test_request(self):
        response = Request(self.test_url, lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())

    def test_LinkItem(self):
        db_name = os.getenv("DATABASE_NAME")
        self.assertTrue(db_name is not None)

        def clear_dbs():
            if os.path.isfile(db_name):
                os.remove(db_name)

        # 1. Init no data
        self.assertEquals(LinkItem.select().count(), 0)
        self.assertEquals(LinkItem.link_to_assets_map(), dict())

        # 2. Insert some data
        asset_a = {"link": ["/b"],
                   "image": [],
                   "css": [],
                   "js": []}
        LinkItem.insert_item("/a", asset_a)
        self.assertEquals(LinkItem.select().count(), 1)
        self.assertEquals(LinkItem.link_to_assets_map(), {"/a": asset_a})

        self.assertTrue("/a" in LinkItem.links_done())
        self.assertTrue("/b" in LinkItem.links_todo())
        self.assertFalse("/a" in LinkItem.links_todo())
        self.assertFalse("/b" in LinkItem.links_done())

        clear_dbs()

    def test_Request(self):
        request = Request(self.test_url)
        request.read_html()
        self.assertTrue("</html>" in request.html)
