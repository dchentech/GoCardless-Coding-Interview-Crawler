#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
os.environ["USE_GOCARDLESS_VERSION_SCRAPY"] = "true"
from gocardless_crawler import GoCardlessWebsiteCrawler, scrapy

scrapy.run(GoCardlessWebsiteCrawler)
