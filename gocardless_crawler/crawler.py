# -*-coding:utf-8-*-

import scrapy
import pdb


class GoCardlessWebsiteCrawler(scrapy.Spider):
    name = 'GoCardless assets sitemap'
    allowed_domains = ["gocardless.com"]
    start_urls = [
        # Explicit indexes which are provided by GoCardless
        'https://gocardless.com/sitemap.xml',
        # The portal, make sure we could access pages that maybe missed in
        # sitemap.xml
        'http://gocardless.com',
    ]

    def parse(self, response):
        for item in self.parse_gocardless_statis_assets(response):
            yield item

        if False:
            pdb.set_trace()

        for href in response.css('a'):
            full_url = response.urljoin(href.select("@href").extract_first())
            yield scrapy.Request(
                full_url,
                callback=self.parse_gocardless_statis_assets)

    def parse_gocardless_statis_assets(self, response):
        for img in response.css("img"):
            yield {"url": response.url,
                   "type": "image",
                   "path": img.select('@src').extract_first()}

        for link in response.css("link"):
            rel = link.xpath("@rel").extract_first()
            path = link.select('@href').extract_first()
            item = {"url": response.url, "path": path}
            if rel == "icon":
                item["type"] = "image/link"
                yield item
            if rel == "stylesheet":
                item["type"] = "css"
                yield item

        for script in response.css("script"):
            path_js = script.select('@src').extract_first()
            if not path_js:  # skip text/javascript
                continue
            yield {"url": response.url, "type": "js", "path": path_js}

    def parse_inner_links(self):
        pass

# TODO extract image/assets from
# https://gocardless.com/bundle/main-22d1be7d280524ff318e.css
# TODO map url => assets
