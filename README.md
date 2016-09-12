GoCardless Coding Interview --- David Chen
==================================


Requirements
----------------------------------
We'd like you to write a simple web crawler, in whatever language you're most comfortable in, which given a URL to crawl, should output a site map, showing the static assets for each page. We'd love it if you could also include a README file which explains your design decisions and any parts you found particularly challenging or interesting.

It should be limited to one domain - so when crawling gocardless.com it would crawl all pages within the gocardless.com domain, but not follow the links to our Facebook and Twitter accounts. We’ll be testing it against gocardless.com.

We will be looking to see if the crawler meets these requirements, and also to see if it meets all and excels at least one of the following areas: robustness, performance, testing, and code structure & layout.


It usually takes around 2 to 3 hours, but don't worry if you feel you want to spend a bit longer on it. Please submit your coding challenge within a week.


The important points from requirements
----------------------------------
* output a site map, showing the static assets for each page
* a README file which explains your design decisions and any parts you found particularly challenging or interesting.
* robustness, performance, testing, and code structure & layout.


Design decisions
----------------------------------
#### Why does this coding interview implement scrapy API?
Because I built the crawler using scrapy in the first version. And
GoCardless said that it's forbidden to use scrapy framework in a crawler
interview question. The parsing code already did the job well, so I don't
want to change it, and then I implement a mock scrapy version.

The differences between implementations are:
1. Original scrapy is x3 faster than this mock. The possible reason is
   scrapy use `Twisted`, and this mock version only use the raw and
   blocking `urllib2`.
2. The mock version crawler more data than original scrapy, though they
  both share the same configuration. See the below "Performance report".
  I don't know why, (and I don't know too much about scrapy, this is the
  first time I use scrapy).
3. This mock version would re-use previous crawler result, but not the
  scrapy (configuration) in the interview project.

#### What is the architecture of scrapy mock?
This scrapy mock consists 4 types of threads:

1. The main thread, manage other threads, fetch start links, etc. See `scrapy_mock.py`
2. Tens of crawler work threads, which accepts `scrapy` API. See `scrapy_threads.py`
3. One sync data thread, which syncs the records and errors to sqlite database. See `scrapy_threads.py`
4. One webui thread, which display the inner current status of scrapy mock process.
   You could visit the webui at http://localhost:8080 . See `scrapy/monitor_webui.py`

The IO storage & flow is:

1. Two tables in sqlite: LinkItem and ErrorLog. See `models.py`
2. `requests_todo.Queue`, main thread would **write** links into it, such as
  start links and previous unfinished links. And tens of crawler worker
  threads would **read** and **write** them, (Locking in memory maybe
  very fast).
3. `link_items_output.Queue` and `errors.Queue`, tens of crawler worker threads would
   **write** records to it, and sync data thread would **read** them and
   write them to sqlite.

See more details at `scrapy_mock.py#work`

#### Why do this project use Python programming language and Scrapy framework?
1. This is a data project, and Python is very good at data processing.
2. Scrapy is the most famous crawler framework, and it's written in
   Python. The requirements also note that this project should meet
   robustness, performance, testing, code structure & layout. So usually
   the best option is to use a mature framework, instead of reinventing a
   wheel or making a demo job.
3. My **production** programming language experiences include Python, Java,
   Ruby, and JavaScript, so I could choose any of them. It just depends.

#### How to make sure this crawler could find out all of pages which belongs to GoCardless?
First, it's not an easy job, because GoCardless.com is a black box. And just like
other data jobs, we need to pay much more time on the dirty ETL job, and
many exceptional situations.

A first mistake is that if a person has no crawler experience, then who would think
starting crawl from the main page GoCardless.com, and then all pages should
be found. But it's wrong, usually many pages would be missed, because
some pages maybe not be linked in the main page or related pages.

The best entrance is the **sitemap.xml**, which is organized by the website itself.
But as you know, **sitemap.xml** is generated by a program, and a
program usually has bugs, so some pages still would be missed. And other
reasons are "sitemap.xml" would ban some unwanted links, or some
paginated pages, or some need-user-login pages, or some Ajax pages, etc.

The supplement tool should be Google Search "site:gocardless.com". If
the pages are visited by people, then Google would index them, or some
people would share them in public social networks. I tried it, but unfortunately, Google
bans search actions program, e.g. `curl https://www.google.com/\#q\=site:gocardless.com\&start\=30` .
So it still needs some works to do about this.




How to run it?
----------------------------------
Run in local

```bash
SCRAPY_VENDOR=mock ./docker-entrypoint.sh
```

Or run in a Docker

```bash
./run.sh
```

And please check the result in `output/result.json` file.


How to run unittest?
----------------------------------
```bash
pip install tox
tox
```


Example result data structure
----------------------------------
#### result.json
```json
{
    "https://developer.gocardless.com/2015-07-06/": {
        "css": [
            "stylesheets/all.css",
            "fonts/fonts.css"
        ],
        "image": [
            "images/mandate-setup.png",
            "images/payment-creation.png",
            "images/oauth-authorize.png"
        ],
        "js": [
            "javascripts/all.js",
            "//www.googletagmanager.com/gtm.js?id=GTM-PRFKNC"
        ]
    },
    "https://gocardless.com/": {
    ...
```

#### result.json.error_log
```json
[
{
"error": "HTTP Error 404: Not Found",
"id": 1,
"link": "https://gocardless.com/es-es/faq/panel-control/creacin-cobros"
},
...
]
```

Performance report [mock version]
----------------------------------
| Section       | Value         | Script                                                                                     |
|---------------|:-------------:|-------------------------------------------------------------------------------------------:|
| Page count    | 9194          | ruby -e 'require "json"; puts JSON.parse(File.read("output/result.json")).size'            |
| Time cost     | 17:12         | time SCRAPY_VENDOR=mock ./docker-entrypoint.sh                                             |
| Crawler speed | 8.9 items/s   |                                                                                            |

1. 50 worker threads cost 17:12 time.
2. 100 worker threads cost 18:44 time.


Performance report [scrapy version]
----------------------------------
| Section       | Value         | Script                                                                                     |
|---------------|:-------------:|-------------------------------------------------------------------------------------------:|
| Page count    | 604           | ruby -e 'require "json"; puts JSON.parse(File.read("output/scrapy_gocardless.json")).size' |
| Time cost     | 25.6 seconds  | time SCRAPY_VENDOR=scrapy ./docker-entrypoint.sh                                           |
| Crawler speed | 23.6 items/s  |                                                                                            |



TODO
----------------------------------
* extract image/assets from https://gocardless.com/bundle/main-22d1be7d280524ff318e.css
* fix dead link (404, 403, ...)
* skip http://gocardless.com/guides/examples/sepa-mandate.pdf
* sqlite performance
* add more unittests
* use asynchronous network api to improve crawler network speed
* is https://gocardless.com/es-es/faq/panel-control/creacin-cobros a valid 404 page?
