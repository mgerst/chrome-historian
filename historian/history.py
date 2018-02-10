import pathlib
import tempfile
from collections import namedtuple
from typing import List, Optional

from historian.utils import hash_file
from .models import database, User, Urls, Visits, VisitSource

UserRecord = namedtuple('UserRecord', 'id,username,hash')


class MultiUserHistory(object):
    """
    Represents a collection of chrome histories. It assumes we have one database per user,
    and will use the filename of the database in the histories folder as the username.

    :ivar str merged_path: The filepath to the merged database
    :ivar dict dbs: Dictionary containing histories
    :ivar str username: Active username (nicer single user history)
    """

    def __init__(self, db_paths, merged_path=None):
        if not merged_path:
            merged_path = tempfile.mkstemp(prefix='historian-combined-')[1]

        # Setup PeeWee with given path
        database.init(merged_path)
        self.merged_path = pathlib.Path(merged_path)
        db_paths = map(pathlib.Path, db_paths)
        self.dbs = {}
        self.find_histories(db_paths)
        self.merge_history()

        # This is needed to make queries work nicer in the frontends for
        # single- vs multi-user  histories
        self.username = None

    def find_histories(self, db_paths: List[pathlib.Path]):
        """
        Load the given histories into the dbs dict.
        """
        for path in db_paths:
            self.dbs[path.name] = path

    def merge_history(self):
        """
        Merge the individual user histories into the merged database.

        Individual user database are hashed so avoid re-merging the histories on every
        run. The merged database will be created if it doesn't already exist.
        """
        print("[Historian] Merging History")
        if not self.merged_path.exists():
            database.connect()
            print("[Historian] Creating merged database")
            database.create_tables([User, Urls, Visits, VisitSource])

        for username, db in self.dbs.items():
            print("[Historian] {}: Loading history for user".format(username))
            hash = hash_file(str(db))

            new = False
            if User.select().where(User.name == username).count() < 1:
                User.create(name=username, hash=hash)
                new = True
            user = User.select().where(User.name == username).get()

            if user.hash == hash and not new:
                print("[Historian] {} already loaded and latest version".format(username))
                continue
            elif not new:
                print("[Historian] {} has changed since last load, re-merging".format(username))
                Urls.delete().where(Urls.user == user).execute()
                Visits.delete().where(Visits.user == user).execute()
                VisitSource.delete().where(VisitSource.user == user).execute()

            # This allows us to perform the import in sqlite, rather than in python
            database.execute_sql("ATTACH ? AS userdb", (str(db),))

            database.execute_sql(
                "INSERT INTO urls (user_id, id, url, title, visit_count, typed_count, last_visit_time, hidden, favicon_id) "
                "SELECT p.id, u.id, u.url, u.title, u.visit_count, u.typed_count, u.last_visit_time, u.hidden, u.favicon_id FROM userdb.urls AS u LEFT JOIN users AS p ON p.name = :username",
                {'username': username})
            database.execute_sql(
                "INSERT INTO visits (user_id, id, url, visit_time, from_visit, transition, segment_id, visit_duration) "
                "SELECT u.id, v.id, v.url, v.visit_time, v.from_visit, v.transition, v.segment_id, v.visit_duration FROM userdb.visits AS v LEFT JOIN users AS u ON u.name = :username",
                {'username': username})
            database.execute_sql(
                "INSERT INTO visit_source (user_id, id, source)  SELECT u.id, v.id, v.source FROM userdb.visit_source AS v LEFT JOIN users AS u ON u.name = :username",
                {'username': username}, require_commit=True)

            database.execute_sql("DETACH userdb")
        database.close()

    def get_users(self) -> List[UserRecord]:
        """
        Get a list of users in the merged database.
        """
        users = User.select()
        return list(users)

    def get_user(self, user_id: Optional[int] = None, username: Optional[str] = None) -> User:
        """
        Get the given user by user id or username.
        """
        if user_id:
            return User.select().where(User.id == user_id).get()
        elif username:
            return User.select().where(User.name == username).get()
        raise RuntimeError("You must specify either user_id or username when calling get_user")

    def get_user_count(self) -> int:
        """
        Get number of users in the merged database.
        """
        return User.select().count()

    def get_url_count(self, username: Optional[str] = None) -> int:
        """
        Get the number of urls in the merged database.

        :param username: Username to filter and count on
        """
        if username:
            user = User.select().where(User.name == username).get()
            return Urls.select().where(Urls.user == user).count()
        else:
            return Urls.select().count()

    def get_url_by_id(self, id: int, user_id: int) -> Urls:
        """
        Get a url by the url id and user id.
        """
        return Urls.select().where(Urls.id == id, Urls.user == user_id).get()

    def get_urls(self, *, username=None, date_lt=None, date_gt=None, url_match=None, title_match=None, limit=None,
                 start=None):
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
        where = []
        query = Urls.select()

        if username:
            user = User.select().where(User.name == username).get()
            where.append(Urls.user == user)
            query = query.join(User)

        if date_lt:
            where.append(Urls.last_visit_time < date_lt)

        if date_gt:
            where.append(Urls.last_visit_time > date_gt)

        if url_match:
            where.append(Urls.url ** '%{}%'.format(url_match))

        if title_match:
            where.append(Urls.title ** '%{}%'.format(title_match))

        if len(where) > 0:
            query = query.where(*where)

        if limit:
            query = query.limit(int(limit))

            if start:
                query = query.offset(int(start))

        return list(query)

    def get_id_for_user(self, username: str) -> int:
        """
        Get the user id for a given username
        """
        return User.select(User.id).where(User.name == username).get().id

    def get_visit_count(self) -> int:
        """
        Get the number of visits for the url.
        """
        return Visits.select().count()

    def get_visit_by_id(self, visit_id: int, user_id: int) -> Visits:
        """
        Get a visit for this url by the visit id and user id.
        """
        return Visits.select().where(Visits.user == user_id, Visits.id == visit_id).get()

    def __str__(self):
        return "<MultiUserHistory merged:{}>".format(self.merged_path)


class History(MultiUserHistory):
    """
    Represents a chrome history file.

    Chrome/Chromium stores history as a sqlite database. It has the following tables
    of interest:

    - urls
    - visits
    - visit_source

    `urls` contains a list of all urls that the browser has in its history. `visits`
    contains a list of every unique visit to the urls in the `urls` table.
    """

    def __init__(self, db_path: str, name: str):
        super().__init__([db_path])
        self.user = User.select().where(User.name == name).get()

    def get_url_count(self, **kwargs) -> int:
        """
        Get number of urls in the history
        """
        return super().get_url_count(self.user.name)

    def get_url_by_id(self, id: int, **kwargs) -> Urls:
        """
        Get a url by its id
        """
        return super().get_url_by_id(id, self.user.id)

    def get_urls(self, *, date_lt=None, date_gt=None, url_match=None, title_match=None, limit=None,
                 start=None, **kwargs) -> List[Urls]:
        return super().get_urls(username=self.user.name, date_lt=date_lt, date_gt=date_gt, url_match=url_match,
                                title_match=title_match, limit=limit, start=start)

    @property
    def db_path(self) -> str:
        """
        The filepath of the history db
        """
        return self.dbs[self.user.name]

    def __str__(self):
        return "<History path:{}>".format(self.db_path)
