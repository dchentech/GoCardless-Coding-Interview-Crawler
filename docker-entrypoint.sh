#!/bin/bash

RESULT_JSON=output/result.json
SCRAPY_OUTPUT_JSON=output/scrapy_gocardless.json


rm -f $SCRAPY_OUTPUT_JSON

pip install -r requirements.txt

scrapy runspider gocardless_crawler/crawler.py --output $SCRAPY_OUTPUT_JSON
./bin/clean_result.py $SCRAPY_OUTPUT_JSON $RESULT_JSON
