# -*-coding:utf-8-*-

from peewee import SqliteDatabase, Model, IntegerField, CharField, \
    BooleanField

peewee_false = False
peewee_true = True


class UrlItem(Model):
    id = IntegerField(index=True, primary_key=True)
    url = CharField()  # could be duplicated
    is_processed = BooleanField(index=True, default=False)

    class Meta:
        database = None
    meta_cls = Meta

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
    def init_db_and_table(cls, db_name):
        # Thread-safe
        db = SqliteDatabase(db_name, threadlocals=True)

        cls.meta_cls.database = db

        db.connect()
        if not cls.table_exists():
            cls.create_table()
