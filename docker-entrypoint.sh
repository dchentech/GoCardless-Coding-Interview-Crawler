#!/bin/bash

set -e

export RESULT_JSON="output/result.json"
export SCRAPY_OUTPUT_JSON="output/scrapy_gocardless.json"
export DATABASE_NAME="crawler_gocardless_production.db"
export SCRAPY_VENDOR=$SCRAPY_VENDOR


# Clean previous result
rm -f $SCRAPY_OUTPUT_JSON
rm -f $RESULT_JSON


python setup.py install


# Run spider to collect links data
if [[ $SCRAPY_VENDOR == "mock" ]]; then
  echo "Use GoCardless demo version of Scrapy ..."
  ./bin/gocardless_scrapy.py
  ./bin/dump_result.py $RESULT_JSON
  echo "Please checkout $RESULT_JSON ..."
else
  echo "Use https://github.com/scrapy/scrapy ..."
  scrapy runspider gocardless_crawler/crawler.py --output $SCRAPY_OUTPUT_JSON
  echo "Please checkout $SCRAPY_OUTPUT_JSON ..."
fi
