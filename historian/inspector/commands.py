import cmd
import shlex
import shutil
from pathlib import Path

from subprocess import Popen, PIPE
from terminaltables import AsciiTable

from historian.exceptions import DoesNotExist
from historian.history import History, MultiUserHistory
from historian.inspector import utils
from historian.utils import get_dbs


class BaseShell(cmd.Cmd):
    custom_prompt = None

    def get_prompt(self):
        return False

    @property
    def prompt(self):
        pmpt = self.get_prompt()

        if not pmpt and self.custom_prompt:
            pmpt = self.custom_prompt
        elif not pmpt:
            pmpt = 'historian> '
        return pmpt

    def do_exit(self, arg):
        """Quits the inspector"""
        return True

    def do_quit(self, arg):
        """Alias for exit"""
        return self.do_exit(arg)

    def spawn_subshell(self, clz, *args, **kwargs):
        if isinstance(clz, type(SubShell)):
            ss = clz(self, *args, **kwargs)
            ss.cmdloop()

    @staticmethod
    def page_output(output, output_height=None):
        term_size = shutil.get_terminal_size((80, 20))
        if not output_height:
            output_height = len(output.split('\n'))

        if term_size.lines < output_height:
            process = Popen(["less"], stdin=PIPE)

            try:
                process.stdin.write(output.encode('utf-8'))
                process.communicate()
            except IOError as e:
                pass
        else:
            print(output)


class SubShell(BaseShell):
    intro = None

    def __init__(self, parent, *args, **kwargs):
        """
        :param BaseShell parent:
        :return:
        """
        super(SubShell, self).__init__(*args, **kwargs)
        self.parent = parent

    def cleanup(self):
        pass

    def do_up(self, arg, propagate=False):
        """go back"""
        self.cleanup()

        # If propagate is set, we want to fully quit
        if propagate:
            self.parent.cmdqueue.append("quit")

        return True

    def do_exit(self, args):
        """quit"""
        return self.do_up(args, True)

    def do_quit(self, args):
        """quit"""
        return self.do_up(args, True)


class InspectorShell(BaseShell):
    intro = 'Chrome Historian Inspector.  Type help or ? to list commands.\n'
    hist = None

    def __init__(self, pargs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_args = pargs
        history_path = Path(pargs.histories)
        if history_path.is_dir():
            dbs = get_dbs(history_path)
            self.hist = MultiUserHistory(dbs, pargs.merged)
        else:
            username = history_path.name
            self.hist = History(pargs.histories, username)

    def get_prompt(self):
        pmpt = "historian"
        if self.hist:
            if isinstance(self.hist, History):
                pmpt += " [{}*]".format(self.hist.db_path)
            else:
                pmpt += " [{}]".format(self.hist.merged_path)

        return pmpt + "> "

    def do_load(self, arg):
        """load HISTORY USERNAME"""
        parts = arg.split()
        if len(parts) != 2:
            print("[!!] Invalid number of arguments: load HISTORY USERNAME")
        history, username = parts
        self.hist = History(history, username)

    def do_unload(self, arg):
        """Unloads the current history"""
        self.hist.close()
        self.hist = None

    def do_db(self, arg):
        """Switch contexts to the History Shell"""
        if self.hist:
            self.spawn_subshell(HistoryShell, hist=self.hist)
        else:
            print("[!!] No Loaded DB")

    def do_enter(self, arg):
        """Switch contexts to the History Shell"""
        self.do_db(arg)


class HistoryShell(SubShell):
    custom_prompt = "historian>DB> "

    def __init__(self, parent, hist, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.hist = hist

    def do_user(self, arg):
        """Load the history for the given user"""
        try:
            user_id = int(arg)
            user = self.hist.get_user(user_id=user_id)
        except ValueError:
            user = self.hist.get_user(username=arg)
        self.spawn_subshell(UserShell, hist=self.hist, user=user)

    def do_merge(self, arg):
        """
        merge HISTORYPATH [USERNAME]

        Merges the specified history into the multi user history
        """
        if isinstance(self.hist, History):
            print("[!!] Not Valid for MultiUserHistory")
            return

    def do_list(self, arg):
        """Lists the available users"""
        users = self.hist.get_users()
        users = [[user.id, user.name] for user in users]
        users = [["ID", "Username"]] + users
        table = AsciiTable(users, "All Users")
        print(table.table)

    def do_stats(self, arg):
        """Lists some statistics about the merged database"""
        user_count = self.hist.get_user_count()
        url_count = self.hist.get_url_count()
        visit_count = self.hist.get_visit_count()
        table = AsciiTable([
            ["Users", user_count],
            ["Urls", url_count],
            ["Visits", visit_count]
        ], "Stats")
        table.inner_heading_row_border = False
        print(table.table)

    def do_search(self, args):
        """
        search TYPE CRITERIA

            TYPE := url|title
            TYPE determines what type of entity is being searched.

            CRITERIA is what to search against.

        Example:
            search url github.com
            search title "API Reference"
        """
        parts = shlex.split(args)
        if len(parts) != 2:
            print("[!!] Usage: search TYPE CRITERIA")
            return
        type, predicate = parts

        if type == "url":
            urls = self.hist.get_urls(url_match=predicate)
        elif type == "title":
            urls = self.hist.get_urls(title_match=predicate)
        else:
            print("[!!] Invalid type")
            return

        urls = [[url.user.name, url.id, url.url[:80], url.title[:80]] for url in urls]
        urls = [["USER", "ID", "URL", "TITLE"]] + urls
        table = AsciiTable(urls, "Search Results")
        self.page_output(table.table, len(urls))


class UserShell(SubShell):
    def __init__(self, parent, hist, user, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.hist = hist
        self.user = user
        self._last_url = None

    def get_prompt(self):
        return "historian>DB ({})>".format(self.user.name)

    def do_search(self, args):
        """
        search TYPE CRITERIA

            TYPE := url|title
            TYPE determines what type of entity is being searched.

            CRITERIA is what to search against.

        Example:
            search url github.com
            search title "API Reference"
        """
        parts = shlex.split(args)
        if len(parts) != 2:
            print("[!!] Usage: search TYPE CRITERIA")
            return
        type, predicate = parts

        if type == "url":
            urls = self.hist.get_urls(username=self.user.name, url_match=predicate)
        elif type == "title":
            urls = self.hist.get_urls(username=self.user.name, title_match=predicate)
        else:
            print("[!!] Invalid type")
            return

        urls = [[url.id, url.url[:80], url.title[:80]] for url in urls]
        urls = [["ID", "URL", "TITLE"]] + urls
        table = AsciiTable(urls, "Search Results")
        self.page_output(table.table, len(urls))

    def do_url(self, args):
        """
        url URLID|URL

            URLID - The ID of the url
            URL - The text of the url, will cause a search.

        View a url based on either the URL or the ID of the url.
        """
        try:
            url_id = int(args)
            url = self.hist.get_url_by_id(url_id, self.user.id)
            utils.print_url(url, True)
            self._last_url = url_id
        except ValueError as _:
            urls = self.hist.get_urls(username=self.user.name, url_match=args)
            if len(urls) == 1:
                utils.print_url(urls[0], True)
            else:
                urls = [[url.id, url.url[:80], url.title[:80]] for url in urls]
                urls = [["ID", "URL", "TITLE"]] + urls
                table = AsciiTable(urls, "Search Results")
                self.page_output(table.table, len(urls))

    def do_inspect(self, args):
        if not args and self._last_url:
            url = self.hist.get_url_by_id(self._last_url, user_id=self.user.id)
            self.spawn_subshell(URLShell, hist=self.hist, user=self.user, url=url)
        elif args:
            try:
                url_id = int(args)
            except ValueError:
                print("[!!] You must specify the url by ID when using inspect")
                return
            url = self.hist.get_url_by_id(url_id, user_id=self.user.id)
            self.spawn_subshell(URLShell, hist=self.hist, user=self.user, url=url)
        else:
            print("[!!] No url id given, and no last url to inspect")


class URLShell(SubShell):
    def __init__(self, parent, hist, user, url, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.hist = hist
        self.user = user
        self.url = url

    def get_prompt(self):
        return "hist>({})>url {}>".format(self.user.name, self.url.id)

    def do_info(self, args):
        utils.print_url(self.url, True)

    def do_visits(self, args):
        visits = self.url.visits
        visits = [[visit.id, visit.visited, visit.transition_core, visit.transition_qualifier, visit.from_visit] for visit in visits]
        visits = [["ID", "TIME", "TYPE", "FLAGS", "FROM"]] + visits
        table = AsciiTable(visits, "Visits for URL {}".format(self.url.id))
        self.page_output(table.table, len(visits) + 3)

    def do_url(self, args):
        self.cleanup()
        self.parent.cmdqueue.append("inspect {}".format(args))
        return True


class DBShell(SubShell):
    custom_prompt = "historian>DB> "
    url = None
    visit = None

    def __init__(self, parent, hist, *args, **kwargs):
        """
        :param History hist: A loaded history instance
        :return:
        """
        super(DBShell, self).__init__(parent, *args, **kwargs)
        if not isinstance(hist, (History, MultiUserHistory)):
            hist = History(hist)

        self.hist = hist

    def get_prompt(self):
        if not self.url and not self.visit:
            return False

        if self.visit and self.url:
            return 'historian>DB (url {},visit {})> '.format(self.url.id, self.visit.id)

        if self.visit:
            return 'historian>DB (visit {})> '.format(self.visit.id)

        if self.url:
            return 'historian>DB (url {})> '.format(self.url.id)

        return self.custom_prompt

    def do_url(self, arg):
        parts = arg.split()
        url_id = username = None
        if len(parts) == 2:
            url_id, username = parts
        elif len(parts) == 1:
            url_id = parts[0]
        else:
            print("[!!] Invalid number of arguments: url URLID [USERNAME]")

        try:
            user_id = self.hist.get_id_for_user(username)
            url = self.hist.get_url_by_id(url_id, user_id=user_id)
        except DoesNotExist as e:
            print(e)
            return False

        utils.print_url(url)

    def do_visits(self, arg):
        if not arg and not self.url:
            print("This command requires a url: inspect [URL ID]")

        if not arg and self.url:
            url = self.url
        else:
            try:
                url = self.hist.get_url_by_id(arg)
            except DoesNotExist as e:
                print(e)
                return False

        print("Url: ", url.url)
        for visit in url.visits:
            print("-" * 25)
            utils.print_visit(visit)

    def do_visit(self, arg):
        try:
            visit = self.hist.get_visit_by_id(arg)
        except DoesNotExist as e:
            print(e)
            return False

        utils.print_visit(visit)

    def do_find_url(self, args):
        """Find URls by Name"""
        urls = self.hist.get_urls(url_match=args)
        if not urls:
            print("No URLs found that match: {}".format(args))
            return False

        print("Found {} Urls:".format(len(urls)))
        for url in urls:
            print("-" * 25)
            utils.print_url(url)

    def do_inspect_url(self, args):
        """Switch to a url inspection context: inspect [URL ID]"""
        if self.visit:
            url = self.visit.url
        else:
            try:
                url = self.hist.get_url_by_id(args)
            except DoesNotExist as e:
                print(e)
                return False

        self.url = url

    def do_clear(self, args):
        if self.url:
            self.url = None

        if self.visit:
            self.visit = None

    def do_info(self, args):
        if not self.url and not self.visit:
            print("The info command must be run in the url or visit context")
            return False

        if self.url:
            utils.print_url(self.url, full=True)

        if self.url and self.visit:
            print('-' * 25)

        if self.visit:
            utils.print_visit(self.visit, full=True)

    def do_inspect_visit(self, args):
        try:
            visit = self.hist.get_visit_by_id(args)
        except DoesNotExist as e:
            print(e)
            return False

        self._update_visit(visit)

    def do_visit_up(self, args):
        if not self.visit:
            print("visit_up must be used in a visit context")
            return False

        if self.visit.from_visit is None:
            print("Current visit has no parent")
            return False

        self._update_visit(self.visit.from_visit)
        self.do_info(None)

    def _update_visit(self, visit):
        self.visit = visit

        if self.url and self.url is not visit.url:
            self.url = visit.url
