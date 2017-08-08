import sqlite3
import datetime
import os
import tempfile

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from historian import models
from historian.exceptions import DoesNotExist


class MultiUserHistory(object):
    def __init__(self, db_paths, merged_path=None):
        mkdb = True
        if not merged_path:
            merged_path = tempfile.mkstemp(prefix='historian-combined-')[1]
        elif os.path.exists(merged_path):
            mkdb = False

        self.merged_path = merged_path
        self.db_paths = db_paths
        self.dbs = {}
        self._db = None

        self.engine = create_engine("sqlite:////{}".format(self.merged_path), convert_unicode=True)
        self.db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

        if mkdb:
            print("[Historian] Merging History")
            self.merge_history()
        else:
            print("[Historian] Using existing merged history")

        self.merge_history()

    def merge_history(self):
        models.Base.metadata.create_all(self.engine)
        for username, db in self.dbs.items():
            print("[Historian] {}: Loading history for user".format(username))
            u = models.User(username=username)
            self.db_session.add(u)

            c = db.db.cursor()
            urls = c.execute("SELECT * FROM urls").fetchall()

            urlmap = {}

            for url in urls:
                url = {
                    'username': username,
                    'user_id': url[0],
                    'url': url[1],
                    'title': url[2],
                    'visit_count': url[3],
                    'typed_count': url[4],
                    'last_visit_time': url[5],
                    'hidden': url[6],
                    'favicon_id': url[7],
                }

                url = models.Url(user=u, local_id=url['user_id'], url=url['url'], title=url['title'],
                                 visit_count=url['visit_count'], typed_count=url['typed_count'],
                                 last_visit_time=url['last_visit_time'], hidden=url['hidden'],
                                 favicon_id=url['favicon_id'])
                self.db_session.add(url)
                urlmap[url.local_id] = url

            visits = c.execute("SELECT * FROM visits").fetchall()

            for visit in visits:
                visit = {
                    'username': username,
                    'user_id': visit[0],
                    'url': visit[1],
                    'visit_time': visit[2],
                    'from_visit': visit[3],
                    'transition': visit[4],
                    'segment_id': visit[5],
                    'visit_duration': visit[6],
                }

                u = urlmap[visit['url']]
                v = models.Visit(local_id=visit['user_id'], url=u, visit_time=visit['visit_time'],
                                 from_visit_id=visit['from_visit'], transition=visit['transition'],
                                 segment_id=visit['segment_id'], visit_duration=visit['visit_duration'])
                self.db_session.add(v)

            self.db_session.commit()

            visits = self.db_session.query(models.Visit).join(models.Url).join(models.User).filter(
                models.User.username == username).all()

            print("[Historian] {}: Updating from visits".format(username))
            for visit in visits:
                self.db_session.query(models.Visit).filter_by(from_visit_id=visit.local_id).update({
                    "from_visit_id": visit.id}, synchronize_session=False)

            self.db_session.commit()
            print("[Historian] {}: Loaded history".format(username))

    @property
    def db(self):
        if not self._db:
            self._db = sqlite3.connect(self.merged_path)
        return self._db

    def get_users(self):
        return self.db_session.query(models.User)

    def get_url_count(self, username=None):
        c = self.db.cursor()

        if username:
            return c.execute("SELECT COUNT(*) FROM urls WHERE name=:username", {'username': username}).fetchone()[0]
        else:
            return c.execute("SELECT COUNT(*) FROM urls").fetchone()[0]

    def get_urls(self, username=None, date_lt=None, date_gt=None, url_match=None, title_match=None, limit=None, start=None):
        """
        Retrieve all urls for a given username, if a username is not given, get all urls in all users.

        :param str username: Search in this user's database
        :param int date_lt: Search for all urls last visited before this date
        :param int date_gt: Search for all urls last visited after this date
        :param str url_match: Search for urls matching this pattern
        :param str title_match: Search for urls with titles matching this pattern
        :param int limit:  Restrict search to this many urls
        :param int start: Start the search with this offset, can only be used with `limit`
        """
        c = self.db.cursor()

        sql = "SELECT * FROM urls"
        where = []
        sub = {}
        if username:
            where.append("name = :username")
            sub['username'] = username

        if date_lt:
            where.append("last_visit_time < :date_lt")
            sub['date_lt'] = date_lt

        if date_gt:
            where.append("last_visit_time > :date_gt")
            sub['date_gt'] = date_gt

        if url_match:
            where.append("url LIKE :url_match")
            sub['url_match'] = "%{}%".format(url_match)

        if title_match:
            where.append("title LIKE :title_match")
            sub['title_match'] = "%{}%".format(title_match)

        first = True
        for clause in where:
            if first:
                sql += " WHERE "
                first = False
            else:
                sql += " AND "
            sql += clause

        sql += " ORDER BY last_visit_time DESC"

        if limit:
            sql += " LIMIT :limit"
            sub['limit'] = int(limit)

            if start:
                sql += ", :offset"
                sub['offset'] = int(start)

        c.execute(sql, sub)
        urls = []
        for url in c.fetchall():
            urls.append(Url(url, self.db))

        return urls

    def __str__(self):
        return "<MultiUserHistory merged:{}>".format(self.merged_path)


class History(object):
    """
    Represents a chrome history file.

    Chrome/Chromium stores history as a sqlite database. It has the following tables
    of interest:

    - urls
    - visits

    `urls` contains a list of all urls that the browser has in its history. `visits`
    contains a list of every unique visit to the urls in the `urls` table.
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.urls = []

    def get_url_count(self):
        c = self.db.cursor()

        return c.execute("SELECT COUNT(*) FROM urls").fetchone()[0]

    def get_urls(self, date_lt=None, date_gt=None, url_match=None, title_match=None, limit=None, start=None):
        """
        Retrieve all urls in the history database.

        :param int date_lt: Search for all urls last visited before this date
        :param int date_gt: Search for all urls last visited after this date
        :param str url_match: Search for urls matching this pattern
        :param title_match: Search for urls with titles matching this pattern
        :param int limit: Restrict search to this many urls
        :param int start: Start the search with this offset, can only be used with `limit`
        """
        c = self.db.cursor()

        sql = "SELECT * FROM urls"
        where = []
        sub = {}
        if date_lt:
            where.append("last_visit_time < :date_lt")
            sub['date_lt'] = date_lt

        if date_gt:
            where.append("last_visit_time > :date_gt")
            sub['date_gt'] = date_gt

        if url_match:
            where.append("url LIKE :url_match")
            sub['url_match'] = "%{}%".format(url_match)

        if title_match:
            where.append("title LIKE :title_match")
            sub['title_match'] = "%{}%".format(title_match)

        first = True
        for clause in where:
            if first:
                sql += " WHERE "
                first = False
            else:
                sql += " AND "
            sql += clause

        sql += " ORDER BY last_visit_time DESC"

        if limit:
            sql += " LIMIT :limit"
            sub['limit'] = int(limit)

            if start:
                sql += ", :offset"
                sub['offset'] = int(start)

        c.execute(sql, sub)
        for url in c.fetchall():
            self.urls.append(Url(url, self.db))

        return self.urls

    def get_url_by_id(self, url_id):
        """
        Retrieve an individual url by its ID

        :param int url_id: The id of the url
        :return Url: The url object contructed from the id
        """
        sql = "SELECT * FROM urls WHERE id = ?"
        c = self.db.cursor()
        c.execute(sql, (url_id,))
        row = c.fetchone()
        if not row:
            raise DoesNotExist(Url, url_id)

        return Url(row, self.db)

    def get_visit_by_id(self, visit_id):
        sql = "SELECT * FROM visits WHERE id = ?"
        c = self.db.cursor()
        c.execute(sql, (visit_id,))
        row = c.fetchone()

        url = self.get_url_by_id(row[1])

        return Visit(row, url, self.db)

    def close(self):
        self.db.close()

    def __str__(self):
        return "<History path:{}>".format(self.db_path)


class Url(object):
    def __init__(self, row, db):
        self._db = db
        self._visits = None

        self.id = row[0]
        self.url = row[1]
        self.title = row[2]
        self.visit_count = row[3]
        self.typed_count = row[4]
        self.last_visit_time_raw = row[5]
        self.hidden = row[6]
        self.favicon_id = row[7]

    @property
    def visits(self):
        if not self._visits:
            self._visits = []
            c = self._db.cursor()

            c.execute("SELECT * FROM visits WHERE url = ?", (self.id,))

            for visit in c.fetchall():
                self._visits.append(Visit(visit, self, self._db))

        return self._visits

    @property
    def last_visit_time(self):
        return to_datetime(self.last_visit_time_raw)

    def visit_at(self, time):
        c = self._db.cursor()
        c.execute("SELECT * FROM visits WHERE url = ? AND visit_time = ?", (self.id, time))
        row = c.fetchone()
        return Visit(row, self, self._db)

    @property
    def latest_visit(self):
        return self.visit_at(self.last_visit_time_raw)


class Visit(object):
    def __init__(self, row, url, db):
        self._db = db

        self.id = row[0]
        self.url_id = row[1]
        self.visit_time = row[2]
        self.from_visit_raw = row[3]
        self.transition = row[4]
        self.segment_id = row[5]
        self.visit_duration = row[6]

        if isinstance(url, Url):
            self.url = url
        elif not url:
            c = self._db.cursor()
            row = c.execute("SELECT * FROM urls WHERE id = ?", (self.url_id,)).fetchone()
            self.url = Url(row, self._db)
        else:
            raise TypeError("The url parameter to Visit must be a Url or None")

    @property
    def from_visit(self):
        if self.from_visit_raw == 0:
            return None

        c = self._db.cursor()
        c.execute("SELECT * FROM visits WHERE id = ?", (self.from_visit_raw,))
        row = c.fetchone()
        return Visit(row, None, self._db)

    @property
    def to_visit(self):
        visits = []

        c = self._db.cursor()
        c.execute("SELECT * FROM visits WHERE from_visit = ?", (self.id,))

        for visit in c.fetchall():
            visits.append(Visit(visit, None, self._db))

        return visits

    def __repr__(self):
        if self.from_visit_raw:
            return "<Visit: {}->{} url({})>".format(self.from_visit_raw, self.id, self.url_id)

        return "<Visit: {} url({})>".format(self.id, self.url_id)


def to_datetime(itime):
    """
    :param int itime: A time in microseconds
    :return DateTime: The datetime object that represents the given time
    """
    return datetime.datetime.utcfromtimestamp((float(itime) / 1000000) - 11644473600)
