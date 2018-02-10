import cmd
import shlex
import shutil
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Union, Optional

from terminaltables import AsciiTable

from historian.history import History, MultiUserHistory
from historian.inspector import utils
from historian.utils import get_dbs


class BaseShell(cmd.Cmd):
    """
    The base shell all other inspector shells are derived from.

    Handles exiting, setting the prompt, and other shell utilities.
    """
    #: Statically set a custom prompt
    custom_prompt = None

    def get_prompt(self) -> Union[str, bool]:
        """
        Override to dynamically set the prompt.
        """
        return False

    @property
    def prompt(self) -> str:
        """
        Get the current prompt.

        Correctly handles the difference between :py:meth:`BaseShell.get_prompt` and
        :py:meth:`BaseShell.custom_prompt`.
        """
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
        """
        Spawns a subshell and sets the current shell as the
        subshells parent.

        :param clz: The class of the subshell
        :param args: Any positional arguments for the subshell
        :param kwargs: Any keyword arguments for the subshell
        """
        if isinstance(clz, type(SubShell)):
            ss = clz(self, *args, **kwargs)
            ss.cmdloop()

    @staticmethod
    def page_output(output, output_height: Optional[int] = None):
        """
        Send the given output through a pager if it is larger than
        the terminal height.

        :param output: The output to print
        :param output_height: The height of the output, calculated if not given
        """
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
    """
    The base class for a inspector sub shell.

    Correctly handles exiting the application as well as
    navigating to the parent shell.
    """
    intro = None

    def __init__(self, parent, *args, **kwargs):
        """
        :param BaseShell parent:
        :return:
        """
        super(SubShell, self).__init__(*args, **kwargs)
        self.parent = parent

    def cleanup(self):
        """
        Override in order to do cleanup when exiting this shell.
        """
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
    """
    The main shell, entered on the start.

    Primarily deals with managing the loaded database.
    """
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
    """
    Shell that deals with managing the merged database.
    """
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
    """
    Shell for dealing with a specific user's history.
    """
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
    """
    Shell that gives access to information about a specific url.
    """
    def __init__(self, parent, hist, user, url, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.hist = hist
        self.user = user
        self.url = url
        self._last_visit = None

    def get_prompt(self):
        return "hist>({})>url {}>".format(self.user.name, self.url.id)

    def do_info(self, args):
        """
        Print information about the current url
        """
        utils.print_url(self.url, True)

    def do_visits(self, args):
        """
        List the visits for the current url
        """
        visits = self.url.visits
        visits = [[visit.id, visit.visited, visit.transition_core, visit.transition_qualifier, visit.from_visit] for
                  visit in visits]
        visits = [["ID", "TIME", "TYPE", "FLAGS", "FROM"]] + visits
        table = AsciiTable(visits, "Visits for URL {}".format(self.url.id))
        self.page_output(table.table, len(visits) + 3)

    def do_url(self, args):
        """
        Switch to a new url.

        Same as running:

            up
            inspect <newid>
        """
        self.cleanup()
        self.parent.cmdqueue.append("inspect {}".format(args))
        return True

    def do_visit(self, args):
        """
        Show information about a specific visit
        """
        visit = self.hist.get_visit_by_id(args, user_id=self.user.id)
        utils.print_visit(visit, True)
        self._last_visit = visit.id

    def do_inspect(self, args):
        """
        Span a subshell to inspect the specific visit.
        """
        if not args and self._last_visit:
            visit = self.hist.get_visit_by_id(self._last_visit, user_id=self.user.id)
            self.spawn_subshell(VisitShell, hist=self.hist, user=self.user, url=self.url, visit=visit)
        elif args:
            try:
                visit_id = int(args)
            except ValueError:
                print("[!!] You must specify the visit by ID when using inspect")
                return
            visit = self.hist.get_visit_by_id(visit_id, user_id=self.user.id)
            self.spawn_subshell(VisitShell, hist=self.hist, user=self.user, url=self.url, visit=visit)
        else:
            print("[!!] No visit id given, and not last visit to inspect")


class VisitShell(SubShell):
    """
    Subshell dealing with visit information.
    """
    def __init__(self, parent, hist, user, url, visit, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.hist = hist
        self.user = user
        self.url = url
        self.visit = visit

    def get_prompt(self):
        return "hist>({})>url {}>visit {}>".format(self.user.name, self.url.id, self.visit.id)

    def do_info(self, args):
        """
        Print information about the current visit.
        """
        utils.print_visit(self.visit, True)

    def do_prev(self, args):
        """
        Inspect the current visit's preceding visit.
        """
        visit = self.visit.visit_from
        url = visit.url_obj
        self.visit = visit
        self.url = url
        self.parent._last_visit = visit.id
        self.parent.url = url
