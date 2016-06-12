import sqlite3
import datetime

from historian.exceptions import DoesNotExist


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
