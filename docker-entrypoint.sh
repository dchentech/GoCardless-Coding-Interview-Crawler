#!/bin/bash

set -e

export RESULT_JSON="output/result.json"
export SCRAPY_OUTPUT_JSON="output/scrapy_gocardless.json"
export USE_GOCARDLESS_VERSION_SCRAPY="true"


# Clean previous result
rm -f $SCRAPY_OUTPUT_JSON
rm -f $RESULT_JSON


# Run unittests
#pip install -U tox

python setup.py install

mysql -uroot --host mysql -p'gocardless' -e "CREATE DATABASE IF NOT EXISTS gocardless"


# Run spider to collect links data
if [[ $USE_GOCARDLESS_VERSION_SCRAPY == "true" ]]; then
  echo "Use GoCardless demo version of Scrapy ..."
  ./bin/gocardless_scrapy.py --output $SCRAPY_OUTPUT_JSON
else
  echo "Use https://github.com/scrapy/scrapy ..."
  scrapy runspider gocardless_crawler/crawler.py --output $SCRAPY_OUTPUT_JSON
fi

# Generate the report
./bin/clean_result.py $SCRAPY_OUTPUT_JSON $RESULT_JSON
