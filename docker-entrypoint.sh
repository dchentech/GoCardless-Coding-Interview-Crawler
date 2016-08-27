#!/bin/bash

rm -f output/gocardless.json
scrapy runspider gocardless_crawler/crawler.py --output output/gocardless.json
