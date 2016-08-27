GoCardless Interview
==================================


Requirements
----------------------------------
We'd like you to write a simple web crawler, in whatever language you're most comfortable in, which given a URL to crawl, should output a site map, showing the static assets for each page. We'd love it if you could also include a README file which explains your design decisions and any parts you found particularly challenging or interesting.

It should be limited to one domain - so when crawling gocardless.com it would crawl all pages within the gocardless.com domain, but not follow the links to our Facebook and Twitter accounts. We’ll be testing it against gocardless.com.

We will be looking to see if the crawler meets these requirements, and also to see if it meets all and excels at least one of the following areas: robustness, performance, testing, and code structure & layout.


It usually takes around 2 to 3 hours, but don't worry if you feel you want to spend a bit longer on it. Please submit your coding challenge within a week.


The important points of requirements
----------------------------------
* output a site map, showing the static assets for each page
* a README file
* robustness, performance, testing, and code structure & layout.


How to run it?
----------------------------------
```bash
./run.sh
```

or local

```bash
./docker-entrypoint.sh
```

And please check the result in `output/gocardless.json` file.


Performance
----------------------------------
1. network ...
2. url size, asset items size


TODO
----------------------------------
* extract image/assets from https://gocardless.com/bundle/main-22d1be7d280524ff318e.css


Helpful resources
----------------------------------
* http://stackoverflow.com/questions/22957267/scrapy-crawl-all-sitemap-links
