# -*-coding:utf-8-*-

import json
from peewee import SqliteDatabase, Model, IntegerField, CharField, \
    BooleanField, TextField

peewee_false = False
peewee_true = True

class SingleInstance(object):

    def set_name(self, db_name):
        self.db_name = db_name

    @property
    def db(self):
        # Thread-safe
        return SqliteDatabase(self.db_name, threadlocals=True)
config = SingleInstance()


class CommonAPI():

    class Meta:
        database = None
    meta_cls = Meta

    @classmethod
    def init_db_and_table(cls, db_name):
        config.set_name(db_name)
        db = config.db

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
        item = cls.select().where(cls.is_processed == peewee_false).first()
        if item is None:
            return None
        else:
            cls.update(is_processed=True).where(cls.id == item.id).execute()
            return item

    @classmethod
    def read_all(cls):
        return list(cls.select().where(cls.is_processed == peewee_false))

    @classmethod
    def finished_urls(cls):
        query = cls.select().where(cls.is_processed == peewee_true)
        return [i.url for i in query]


class UrlAssets(Model, CommonAPI):
    id = IntegerField(index=True, primary_key=True)
    url = CharField(unique=True, index=True)
    assets = TextField()

    @classmethod
    def upsert(cls, url, _assets):
        is_created = cls.select().where(cls.url == url).limit(1).count() == 1
        if not is_created:
            cls.create(url=url, assets=json.dumps(_assets))

    @classmethod
    def read_all(cls):
        result = []
        for i in cls.select():
            item = {"url": i.url, "assets": json.loads(i.assets)}
            result.append(item)
        return result


__all__ = ["UrlItem", "UrlAssets"]
