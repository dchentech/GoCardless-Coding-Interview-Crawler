FROM ubuntu:14.04


RUN apt-get update -y
RUN apt-get install -y python python-pip python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev
RUN pip install lxml && pip install pyopenssl && pip install Scrapy

RUN mkdir -p /deploy/gocardless_interview_201608
WORKDIR /deploy/gocardless_interview_201608

ENTRYPOINT ["./docker-entrypoint.sh"]
