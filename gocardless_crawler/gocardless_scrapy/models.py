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
        cls.create(link=_link, assets=json.dumps(_assets))


db.connect()
if not LinkItem.table_exists():
    LinkItem.create_table()


__all__ = ["LinkItem"]
