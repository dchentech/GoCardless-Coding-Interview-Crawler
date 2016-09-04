# -*- coding: utf-8 -*-

import os
import sys
import unittest
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
from gocardless_crawler.gocardless_scrapy.http_request import Request
from gocardless_crawler.gocardless_scrapy.models import UrlItem, UrlAssets


class TestGoCardlessScrapy(unittest.TestCase):

    def test_request(self):
        response = Request("https://gocardless.com/", lambda: True)
        self.assertTrue("GoCardless" in response.css("title").extract_first())

    def test_UrlItem(self):
        db_name = "tests.sqlite"

        def clear_dbs():
            if os.path.isfile(db_name):
                os.remove(db_name)
            if os.path.isfile("peewee.db"):
                os.remove("peewee.db")
        clear_dbs()

        UrlItem.init_db_and_table(db_name)
        UrlAssets.init_db_and_table(db_name)

        first_count = UrlItem.unfinished_count()

        # 1. insert an item
        first_item = {"url": "a"}
        UrlItem.create(**first_item)
        seconds_count = UrlItem.unfinished_count()
        self.assertEqual(seconds_count, first_count + 1)

        # 2. read an item
        self.assertEqual(UrlItem.get().url, first_item["url"])
        self.assertEqual(UrlItem.unfinished_count(), first_count)

        # 3. insert two items
        UrlItem.create(**{"url": "b"})
        UrlItem.create(**{"url": "c"})
        two_items = UrlItem.read_all()
        self.assertEqual(len(two_items), 2)
        self.assertTrue(UrlItem.is_empty)

        assets = {"image": [], "js": [], "css": []}
        UrlAssets.upsert("/a", assets)
        expected_assets = [{"url": "/a", "assets": assets}]
        self.assertEqual(UrlAssets.select().count(), 1)
        self.assertEqual(UrlAssets.read_all(), expected_assets)

        clear_dbs()
