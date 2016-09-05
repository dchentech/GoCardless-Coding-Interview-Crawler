# -*-coding:utf-8-*-

import os
import time
import json
from peewee import MySQLDatabase, SqliteDatabase
from peewee import Model, IntegerField, CharField, \
    TextField, OperationalError

peewee_false = False
peewee_true = True


class PeeweeUtils(object):

    @staticmethod
    def catch_OperationalError(func):
        result = None
        while True:
            try:
                result = func()
                break
            except OperationalError:
                time.sleep(1)
                pass
        return result


class SingleInstance(object):

    def __init__(self):
        self.conn = None

    def use_db(self, db_type, db_name):
        print "use db_type: %s, db_name: %s" % (db_type, db_name,)
        self.db_type = db_type
        self.db_name = db_name

    @property
    def db(self):
        if self.conn is not None:
            return self.conn

        # Thread-safe
        if self.db_type == "mysql":
            self.conn = MySQLDatabase(self.db_name,
                                      # host="mysql",
                                      host="192.168.99.100",
                                      user="root",
                                      passwd="gocardless",)
        if self.db_type == "sqlite":
            self.conn = SqliteDatabase(self.db_name, threadlocals=True)

        return self.conn

config = SingleInstance()
config.use_db("mysql", "gocardless")


class CommonAPI():

    class Meta:
        database = config.db
    meta_cls = Meta

    @classmethod
    def init_db_and_table(cls, db_type, db_name):
        config.use_db(db_type, db_name)
        db = config.db
        db.set_autocommit(True)

        cls.meta_cls.database = db


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


__all__ = ["LinkItem", "PeeweeUtils"]
