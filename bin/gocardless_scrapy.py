#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
os.environ["SCRAPY_VENDOR"] = "mock"
from gocardless_crawler import GoCardlessWebsiteCrawler, scrapy

scrapy.run(GoCardlessWebsiteCrawler)
