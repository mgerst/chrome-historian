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
    """
    A user that has a history in the database.
    """
    id = IntegerField(primary_key=True)
    name = CharField(unique=True)
    hash = TextField()

    class Meta:
        db_table = 'users'


class Urls(BaseModel):
    """
    A URL in the history.
    """
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
        """
        A collection of visits related to this url.
        """
        if not hasattr(self, '_visits'):
            self._visits = None

        if not self._visits:
            self._visits = list(Visits.select().where(Visits.user == self.user, Visits.url == self.id))

        return self._visits

    @property
    def last_visit(self) -> datetime.datetime:
        """
        The last visit of this URL represented as a datetime object.
        """
        return webkit_datetime(self.last_visit_time)

    def visit_at(self, time: int) -> 'Visits':
        """
        Get a reference to the URL visit at the given timestamp.

        :param int: The timestamp in webkit format
        """
        visit = Visits.select().where(Visits.user == self.user, Visits.visit_time == time).get()
        return visit

    @property
    def latest_visit(self) -> 'Visits':
        """
        Get a reference to the URL visit at the most recent visit.
        """
        return self.visit_at(self.last_visit_time)

    class Meta:
        db_table = 'urls'
        indexes = (
            (('user', 'id'), True),
        )
        primary_key = CompositeKey('id', 'user')


class Visits(BaseModel):
    """
    A visit to a particular :py:class:`Urls`.
    """
    user = ForeignKeyField(User, db_column='user_id', related_name='visits')
    id = IntegerField()
    url = IntegerField()
    transition = IntegerField()
    segment = IntegerField(db_column='segment_id')
    from_visit = IntegerField()
    visit_duration = IntegerField()
    visit_time = IntegerField()

    @property
    def transition_core(self) -> 'TransitionCore':
        """
        The transition value with the TRANSITION_CORE_MASK applied.
        """
        core = self.transition & TransitionCore.MASK
        return TransitionCore(core)

    @property
    def transition_qualifier(self) -> 'TransitionQualifier':
        """
        The transition value with the TRANSITION_QUALIFIER_MASK applied.
        """
        qualifier = self.transition & TransitionQualifier.MASK
        return TransitionQualifier(qualifier)

    @property
    def visit_from(self) -> Optional['Visits']:
        """
        The visit preceding this one.
        """
        if self.from_visit == 0:
            return None
        return Visits.select().where(Visits.id == self.from_visit).get()

    @property
    def visits_to(self) -> List['Visits']:
        """
        A list of visits with this visit as the preceding visit.
        """
        return list(Visits.select().where(Visits.user == self.user, Visits.from_visit == self.id))

    @property
    def url_obj(self) -> Urls:
        """
        Get a reference to the :py:class:`Urls` object associated with this visit.
        """
        return Urls.select().where(Urls.user == self.user, Urls.id == self.url).get()

    @property
    def visited(self) -> datetime.datetime:
        """
        The datetime representation of the time this Visit occurred.
        """
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
    """
    How a visit came to be.

    See :py:class:`VisitSourceEnum`.
    """
    user = ForeignKeyField(User, db_column='user_id', related_name='visit_sources')
    id = IntegerField()
    source = IntegerField()

    @property
    def visit_source(self) -> 'VisitSourceEnum':
        """
        The source of a visit (imported history, chrome sync, etc.)
        """
        return VisitSourceEnum(self.source)

    class Meta:
        db_table = 'visit_source'
        indexes = (
            (('user', 'id'), True),
        )
        primary_key = CompositeKey('id', 'user')


class TransitionCore(IntEnum):
    """
    How a visit was generated.
    """

    #: The user clicked a link
    LINK = 0

    #: The user typed the url into the omnibar
    TYPED = 1

    #: The user used a UI suggestion (i.e. the destinations page)
    AUTO_BOOKMARK = 2

    #: The url was loaded automatically in a subframe
    AUTO_SUBFRAME = 3

    #: The url was manually loaded in a subframe (user click)
    MANUAL_SUBFRAME = 4

    #: User typed in url bar and selected non url entry (ex. Search Google for...)
    GENERATED = 5

    #: Specified by command line or was start page
    START_PAGE = 6

    #: User filled a form
    FORM_SUBMIT = 7

    #: User reloaded the page
    RELOAD = 8

    #: Generated from a replaceable keyword other than default search (tab-to-search)
    KEYWORD = 9

    #: Corresponds to a visit generated for a keyword.
    KEYWORD_GENERATED = 10

    #: Bitmask used to retrieve the Core value
    MASK = 0xFF


class TransitionQualifier(IntFlag):
    """
    Additional information about a visit transition.
    """
    #: Navigation was blocked
    BLOCKED = 0x00800000

    #: User used forward or back button to browse history
    FORWARD_BACK = 0x01000000

    #: User used the address bar
    FROM_ADDRESS_BAR = 0x02000000

    #: User navigated to home page
    HOME_PAGE = 0x04000000

    #: Visit generated from API (extensions)
    FROM_API = 0x08000000

    #: Beginning of navigation chain
    CHAIN_START = 0x10000000

    #: End of a redirect chain
    CHAIN_END = 0x20000000

    #: Redirect caused by JS or meta refresh
    CLIENT_REDIRECT = 0x40000000

    #: Redirect caused by HTTP headers
    SERVER_REDIRECT = 0x80000000

    #: Mask used to test for redirects
    IS_REDIRECT_MASK = 0xC0000000

    #: Mask used to get qualifier
    MASK = 0xFFFFFF00


class VisitSourceEnum(IntEnum):
    """
    How a visit came to be in the local history.
    """
    #: From chrome sync
    SYNCED = 0

    #: Locally browsed
    BROWSED = 1

    #: From extension
    EXTENSION = 2

    #: Imported from firefox
    FIREFOX_IMPORTED = 3

    #: Imported from IE
    IE_IMPORTED = 4

    #: Imported from Safari
    SAFARI_IMPORTED = 5
