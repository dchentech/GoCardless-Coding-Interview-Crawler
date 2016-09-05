#!/usr/bin/env python
# -*-coding:utf-8-*-

import sys
import json
from gocardless_crawler.gocardless_scrapy import LinkItem, ErrorLog

def write(content, path):
    print "write to %s" % path
    f = open(path, 'w')
    f.write(content)
    f.close()

RESULT_JSON = sys.argv[1]
ERROR_JSON = "%s.error_log" % RESULT_JSON

# Dump LinkItem table
link_items = LinkItem.link_to_assets_map()
for link, assets in link_items.iteritems():
    del assets["link"]
link_items_content = json.dumps(link_items, indent=4, sort_keys=True)
write(link_items_content, RESULT_JSON)

# Dump ErrorLog table
error_logs = [{"id": i.id, "link": i.link, "error": i.error}
              for i in ErrorLog.select()]
error_logs_content = json.dumps(error_logs, indent=0, sort_keys=True)
write(error_logs_content, ERROR_JSON)
