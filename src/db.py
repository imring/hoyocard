from peewee import *

db = SqliteDatabase('database.db')

class User(Model):
    user_id = IntegerField(unique=True)
    uid = IntegerField()
    ltuid = CharField()
    ltoken = CharField()
    class Meta:
        database = db

db.connect()
db.create_tables([User])