# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler.gocardless_scrapy.http_request import Request
from gocardless_crawler.gocardless_scrapy.models import LinkItem


class TestGoCardlessScrapy(unittest.TestCase):

    def test_request(self):
        response = Request("https://gocardless.com/", lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())

    def test_LinkItem(self):
        db_name = os.getenv("DATABASE_NAME")
        self.assertTrue(db_name is not None)

        def clear_dbs():
            if os.path.isfile(db_name):
                os.remove(db_name)

        # 1. Init no data
        LinkItem.load_previous_status()
        self.assertEquals(LinkItem.select().count(), 0)
        self.assertEquals(LinkItem.link_to_assets_map, dict())

        # 2. Insert some data
        asset_a = {"link": ["/b"],
                   "image": [],
                   "css": [],
                   "js": []}
        LinkItem.insert_item("/a", asset_a)
        self.assertEquals(LinkItem.select().count(), 1)
        LinkItem.load_previous_status()
        self.assertEquals(LinkItem.link_to_assets_map, {"/a": asset_a})

        self.assertTrue(LinkItem.is_link_processed("/a"))
        self.assertFalse(LinkItem.is_link_processed("/b"))
        self.assertFalse(LinkItem.is_link_processed("/nonexistent"))

        clear_dbs()
