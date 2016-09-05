# -*-coding:utf-8-*-

import os
import json
from peewee import SqliteDatabase
from peewee import Model, IntegerField, CharField, \
    TextField


db_name = os.getenv("DATABASE_NAME")
assert db_name is not None
db = SqliteDatabase(db_name, threadlocals=True)


class LinkItem(Model):
    """
    1. Queue.Queue is already fast enough for multiple-threads.
    2. Use a single writing thread to do the database job.
    3. Crawler doesn't require transactional consistency.
       It could re-process any item at any time.
    """
    id = IntegerField(index=True, primary_key=True)
    link = CharField(unique=True)
    assets = TextField()

    class Meta:
        database = db

    @classmethod
    def load_all_data(cls):
        return list(cls.select())

    @classmethod
    def link_to_assets_map(cls):
        result = dict()
        for i in cls.load_all_data():
            result[i.link] = json.loads(i.assets)
        return result

    @classmethod
    def links_done(cls):
        return set(cls.link_to_assets_map().keys())

    @classmethod
    def links_todo(cls):
        result = list()
        done = cls.links_done()
        for link, assets in cls.link_to_assets_map().iteritems():
            for link2 in assets["link"]:
                if link2 not in done:
                    result.append(link2)
        return result

    @classmethod
    def insert_item(cls, _link, _assets):
        query = list(cls.select().where(cls.link == _link).limit(1))
        if query:
            item = query[0]
        else:
            item = cls(link=_link)
        item.assets = json.dumps(_assets)
        item.save()


class ErrorLog(Model):
    id = IntegerField(index=True, primary_key=True)
    link = CharField(unique=False)
    error = TextField()

    @classmethod
    def insert_item(cls, _link, _error):
        cls.create(link=_link, error=_error)

db.connect()
if not LinkItem.table_exists():
    LinkItem.create_table()
if not ErrorLog.table_exists():
    ErrorLog.create_table()


__all__ = ["LinkItem", "ErrorLog"]
