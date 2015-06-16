from peewee import *
from database import *

dbproxy = Proxy()

class Base(Model):
    class Meta:
        database = dbproxy

class User(Base):
    id = PrimaryKeyField()
    name = CharField(unique=True, null=False, index=True)
    confirmed = BooleanField(default=False, null=False)
    github_id = MSQLIntegerField(unsigned=True, null=True)
    homepage_url = CharField(default=None, null=True)
    avatar_url = CharField(default=None, null=True)
    email = CharField(default=None, null=True)
    # salt = CharField(...)
    # ...

class Token(Base):
    id = PrimaryKeyField()
    value = CharField(unique=True, null=False, index=True)
    user = ForeignKeyField(User, related_name="tokens", null=False)
    seen = BooleanField(default=False, null=False)
    desc = CharField(null=False)

class Repo(Base):
    id = PrimaryKeyField(null=False)
    user = ForeignKeyField(User, related_name="repos", null=False)
    name = CharField(null=False, index=True)
    desc = CharField(max_length=255)

    class Meta:
        indexes = [(("user", "name"), True)]

class HMap(Base):
    sha = MSQLBinaryField(length=20, primary_key=True)
    val = CharField(max_length=2048, null=False)

class CSet(Base):
    repo = ForeignKeyField(Repo, related_name="csets", null=False)
    hkey = ForeignKeyField(HMap, null=False)
    time = MSQLTimestampField(precision=0, null=False)
    type = MSQLTinyIntegerField(unsigned=True, null=False)
    len  = MSQLMediumIntegerField(unsigned=True, null=False)
    # base = MSQLTimestampField(precision=3, null=False)

    class Meta:
        primary_key = CompositeKey("repo", "hkey", "time")

    SNAPSHOT = 0
    DELTA = 1
    DELETE = 2

# TODO: Store blobs in a dedicated blobstore? (benchmark)

class Blob(Base):
    repo = ForeignKeyField(Repo, related_name="blobs", null=False)
    hkey = ForeignKeyField(HMap, null=False)
    time = MSQLTimestampField(precision=0, null=False)
    data = BlobField()

    class Meta:
        primary_key = CompositeKey("repo", "hkey", "time")

def initialize(database, blobstore):
    dbproxy.initialize(database)
