#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
import sys
import json
from collections import defaultdict


SCRAPY_OUTPUT_JSON = sys.argv[1]
RESULT_JSON = sys.argv[2]


if not os.path.isfile(SCRAPY_OUTPUT_JSON):
    msg = "Please run ./docker-entrypoint.sh to create %s first ..." % \
          SCRAPY_OUTPUT_JSON
    raise Exception(msg)


def convert_to_map(items):
    mapping = defaultdict(lambda: {"js": [], "css": [], "image": []})
    for item in items:
        mapping[item["url"]][item["type"]].append(item["path"])

    return json.dumps(mapping, indent=4, sort_keys=True)


with open(SCRAPY_OUTPUT_JSON) as data_file:
    items = json.load(data_file)
    result = convert_to_map(items)

    f = open(RESULT_JSON, 'w')
    f.write(result)
    f.close()
