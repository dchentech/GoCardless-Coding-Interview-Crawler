# -*-coding:utf-8-*-

import os
import urllib2
from bs4 import BeautifulSoup

if os.getenv('USE_GOCARDLESS_VERSION_SCRAPY') == "true":
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
        yield self.parse_gocardless_static_assets(response)

        for href in response.css('a'):
            full_url = response.urljoin(href.xpath("@href").extract_first())
            yield Request(
                full_url,
                callback=self.parse_gocardless_static_assets)

    def parse_gocardless_static_assets(self, response):
        assets = {"image": [], "css": [], "js": []}
        result = {"link": response.url, "assets": assets}

        for img in response.css("img"):
            assets["image"].append(img.xpath('@src').extract_first())

        for link in response.css("link"):
            rel = link.xpath("@rel").extract_first()
            path = link.xpath('@href').extract_first()
            if rel == "icon":
                assets["image"].append(path)
            if rel == "stylesheet":
                assets["css"].append(path)

        for script in response.css("script"):
            path_js = script.xpath('@src').extract_first()
            if not path_js:  # skip text/javascript
                continue
            assets["js"].append(path_js)

        return result

    @property
    def sitemap_urls(self):
        # Explicit indexes which are provided by GoCardless
        sitemap_xml = 'https://gocardless.com/sitemap.xml'

        soup = BeautifulSoup(urllib2.urlopen(sitemap_xml), "lxml")
        return [loc.text for loc in soup.select("loc")]
