from enum import IntFlag, IntEnum

import datetime
from typing import Optional, List

from peewee import *

from .utils import webkit_datetime

database = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField(unique=True)
    hash = TextField()

    class Meta:
        db_table = 'users'


class Urls(BaseModel):
    user = ForeignKeyField(User, db_column='user_id', related_name='urls')
    id = IntegerField()
    url = TextField()
    title = TextField()
    visit_count = IntegerField()
    typed_count = IntegerField()
    last_visit_time = IntegerField()
    hidden = IntegerField()
    favicon_id = IntegerField()

    @property
    def visits(self):
        if not hasattr(self, '_visits'):
            self._visits = None

        if not self._visits:
            self._visits = list(Visits.select().where(Visits.user == self.user, Visits.url == self.id))

        return self._visits

    @property
    def last_visit(self) -> datetime.datetime:
        return webkit_datetime(self.last_visit_time)

    def visit_at(self, time: int) -> 'Visits':
        visit = Visits.select().where(Visits.user == self.user, Visits.visit_time == time).get()
        return visit

    @property
    def latest_visit(self) -> 'Visits':
        return self.visit_at(self.last_visit_time)

    class Meta:
        db_table = 'urls'
        indexes = (
            (('user', 'id'), True),
        )
        primary_key = CompositeKey('id', 'user')


class Visits(BaseModel):
    user = ForeignKeyField(User, db_column='user_id', related_name='visits')
    id = IntegerField()
    url = IntegerField()
    transition = IntegerField()
    segment = IntegerField(db_column='segment_id')
    from_visit = IntegerField()
    visit_duration = IntegerField()
    visit_time = IntegerField()

    @property
    def transition_core(self):
        core = self.transition & TransitionCore.MASK
        return TransitionCore(core)

    @property
    def transition_qualifier(self):
        qualifier = self.transition & TransitionQualifier.MASK
        return TransitionQualifier(qualifier)

    @property
    def visit_from(self) -> Optional['Visits']:
        if self.from_visit == 0:
            return None
        return Visits.select().where(Visits.id == self.from_visit)

    @property
    def visits_to(self) -> List['Visits']:
        return list(Visits.select().where(Visits.user == self.user, Visits.from_visit == self.id))

    @property
    def url_obj(self) -> Urls:
        return Urls.select().where(Urls.user == self.user, Urls.id == self.url).get()

    @property
    def visited(self) -> datetime.datetime:
        return webkit_datetime(self.visit_time)

    def __repr__(self) -> str:
        visit = self.visit_from
        if visit:
            return "<Visit: {}->{} url({})>".format(self.from_visit, self.id, self.url)
        return "<Visit: {} url({})>".format(self.id, self.url)

    class Meta:
        db_table = 'visits'
        indexes = (
            (('user', 'id'), True),
        )
        primary_key = CompositeKey('id', 'user')


class VisitSource(BaseModel):
    user = ForeignKeyField(User, db_column='user_id', related_name='visit_sources')
    id = IntegerField()
    source = IntegerField()

    @property
    def visit_source(self):
        return VisitSourceEnum(self.source)

    class Meta:
        db_table = 'visit_source'
        indexes = (
            (('user', 'id'), True),
        )
        primary_key = CompositeKey('id', 'user')


class TransitionCore(IntEnum):
    LINK = 0
    TYPED = 1
    AUTO_BOOKMARK = 2
    AUTO_SUBFRAME = 3
    MANUAL_SUBFRAME = 4
    GENERATED = 5
    START_PAGE = 6
    FORM_SUBMIT = 7
    RELOAD = 8
    KEYWORD = 9
    KEYWORD_GENERATED = 10
    MASK = 0xFF


class TransitionQualifier(IntFlag):
    BLOCKED = 0x00800000
    FORWARD_BACK = 0x01000000
    FROM_ADDRESS_BAR = 0x02000000
    HOME_PAGE = 0x04000000
    FROM_API = 0x08000000
    CHAIN_START = 0x10000000
    CHAIN_END = 0x20000000
    CLIENT_REDIRECT = 0x40000000
    SERVER_REDIRECT = 0x80000000
    IS_REDIRECT_MASK = 0xC0000000
    MASK = 0xFFFFFF00


class VisitSourceEnum(IntEnum):
    SYNCED = 0
    BROWSED = 1
    EXTENSION = 2
    FIREFOX_IMPORTED = 3
    IE_IMPORTED = 4
    SAFARI_IMPORTED = 5
