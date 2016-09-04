#!/bin/bash

RESULT_JSON=output/result.json
SCRAPY_OUTPUT_JSON=output/scrapy_gocardless.json


rm -f $SCRAPY_OUTPUT_JSON

pip install -U tox
tox

if [[ $USE_GOCARDLESS_VERSION_SCRAPY == "true" ]]; then
  echo "Use GoCardless demo version of Scrapy ..."
  ./bin/gocardless_scrapy.py --output $SCRAPY_OUTPUT_JSON
else
  echo "Use https://github.com/scrapy/scrapy ..."
  scrapy runspider gocardless_crawler/crawler.py --output $SCRAPY_OUTPUT_JSON
fi

./bin/clean_result.py $SCRAPY_OUTPUT_JSON $RESULT_JSON
