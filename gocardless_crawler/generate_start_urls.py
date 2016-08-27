# -*-coding:utf-8-*-

import json
import scrapy
import os
import pdb


class GoCardlessStartUrls(object):

    default_urls = [
        # Explicit indexes which are provided by GoCardless
        'https://gocardless.com/sitemap.xml',
        # The portal, make sure we could access pages that maybe missed in
        # sitemap.xml
        'http://gocardless.com',
    ]

    google_urls_file = "output/google_urls.json"

    @property
    def urls(self):
        return self.default_urls + self.google_urls

    @property
    def google_urls(self):
        if not os.path.isfile(self.google_urls_file):
            raise "Please run first..."  # TODO

        urls = []
        with open(self.google_urls_file) as json_data:
            urls = json.load(json_data)
        return urls


class GoCardlessGoogleUrlsCrawler(scrapy.Spider):
    name = 'GoCardless google urls'

    # Because Google bans searching from Scrapy
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) ' + \
                 'Gecko/20100101 Firefox/39.0'

    @property
    def start_urls(self):
        # e.g. https://www.google.com/#q=site:gocardless.com&start=30
        template = "https://www.google.com/#q=site:gocardless.com&start=%s"
        return [template % (page * 10) for page in xrange(50)]

    def parse(self, response):
        pdb.set_trace()
        response.xpath('//h3/a/@href').extract()
        for item in self.parse_gocardless_statis_assets(response):
            yield item
