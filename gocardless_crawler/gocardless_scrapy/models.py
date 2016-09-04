# -*-coding:utf-8-*-

import time
import json
from peewee import MySQLDatabase, SqliteDatabase
from peewee import Model, IntegerField, CharField, \
    BooleanField, TextField, OperationalError

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

    def use_db(self, db_type, db_name):
        self.db_type = db_type
        self.db_name = db_name

    @property
    def db(self):
        # Thread-safe
        if self.db_type == "mysql":
            return MySQLDatabase("gocardless",
                                 # host="192.168.99.100",
                                 host="mysql",
                                 user="root",
                                 passwd="gocardless",)
        if self.db_type == "sqlite":
            return SqliteDatabase(self.db_name, threadlocals=True)

config = SingleInstance()


class CommonAPI():

    class Meta:
        database = None
    meta_cls = Meta

    @classmethod
    def init_db_and_table(cls, db_type, db_name):
        config.use_db(db_type, db_name)
        db = config.db
        db.set_autocommit(True)

        cls.meta_cls.database = db

        db.connect()
        if not cls.table_exists():
            cls.create_table()


class UrlItem(Model, CommonAPI):
    id = IntegerField(index=True, primary_key=True)
    url = CharField(unique=False)  # could be duplicated
    is_processed = BooleanField(index=True, default=False)

    @classmethod
    def unfinished_count(cls):
        return cls.select().where(cls.is_processed == peewee_false).count()

    @classmethod
    def is_empty(cls):
        return cls.unfinished_count() == 0

    @classmethod
    def get(cls):
        with config.db.atomic():
            item = cls.select().where(cls.is_processed == peewee_false).first()
            if item is None:
                return None
            else:
                cls.update(is_processed=True) \
                   .where(cls.id == item.id).execute()
                return item

    @classmethod
    def read_all(cls):
        return list(cls.select().where(cls.is_processed == peewee_false))

    @classmethod
    def finished_urls(cls):
        query = cls.select().where(cls.is_processed == peewee_true)
        return [i.url for i in query]

    @classmethod
    def finished_urls_count(cls):
        return cls.select().where(cls.is_processed == peewee_true).count()


class UrlAssets(Model, CommonAPI):
    id = IntegerField(index=True, primary_key=True)
    url = CharField(unique=True, index=True)
    assets = TextField()

    @classmethod
    def upsert(cls, url, _assets):
        with config.db.atomic():
            is_created = cls.select().where(cls.url == url).limit(1).count() \
                == 1
            if not is_created:
                cls.create(url=url, assets=json.dumps(_assets))

    @classmethod
    def read_all(cls):
        result = []
        for i in cls.select():
            item = {"url": i.url, "assets": json.loads(i.assets)}
            result.append(item)
        return result

    @classmethod
    def total_count(cls):
        return cls.select().count()


__all__ = ["UrlItem", "UrlAssets", "PeeweeUtils"]
