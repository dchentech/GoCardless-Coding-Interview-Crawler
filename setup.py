from setuptools import setup


setup(
    name='gocardless_crawler',
    version="0.1",
    include_package_data=True,
    zip_safe=False,
    packages=[
        "gocardless_crawler",
        "gocardless_crawler/gocardless_scrapy",
    ],
    install_requires=[
        'lxml',
        'pyopenssl',
        'Scrapy',
        'beautifulsoup4',
        'cherrypy',
        'peewee',
    ],
    scripts=[
        'bin/dump_result.py',
        'bin/gocardless_scrapy.py',
    ],
)
