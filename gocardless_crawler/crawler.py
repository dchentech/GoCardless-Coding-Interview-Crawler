# -*-coding:utf-8-*-

import os
import urllib2
from bs4 import BeautifulSoup

if os.environ['USE_GOCARDLESS_VERSION_SCRAPY'] == "true":
    from .gocardless_scrapy import scrapy, Request
else:
    import scrapy
    from scrapy.http.request import Request


class GoCardlessWebsiteCrawler(scrapy.Spider):
    name = 'GoCardless assets sitemap'
    allowed_domains = ["gocardless.com"]

    start_urls = [
        # The portal. Make sure we could access pages that maybe missed in
        # sitemap.xml
        'http://gocardless.com',
    ]

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self.parse)

    def parse(self, response):
        for item in self.parse_gocardless_static_assets(response):
            yield item

        for href in response.css('a'):
            full_url = response.urljoin(href.select("@href").extract_first())
            yield scrapy.Request(
                full_url,
                callback=self.parse_gocardless_static_assets)

    def parse_gocardless_static_assets(self, response):
        for img in response.css("img"):
            yield {"url": response.url,
                   "type": "image",
                   "path": img.select('@src').extract_first()}

        for link in response.css("link"):
            rel = link.xpath("@rel").extract_first()
            path = link.select('@href').extract_first()
            item = {"url": response.url, "path": path}
            if rel == "icon":
                item["type"] = "image"
                yield item
            if rel == "stylesheet":
                item["type"] = "css"
                yield item

        for script in response.css("script"):
            path_js = script.select('@src').extract_first()
            if not path_js:  # skip text/javascript
                continue
            yield {"url": response.url, "type": "js", "path": path_js}

    @property
    def sitemap_urls(self):
        # Explicit indexes which are provided by GoCardless
        sitemap_xml = 'https://gocardless.com/sitemap.xml'

        soup = BeautifulSoup(urllib2.urlopen(sitemap_xml), "lxml")
        return [loc.text for loc in soup.select("loc")]
