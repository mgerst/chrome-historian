import cmd

from historian.exceptions import DoesNotExist
from historian.history import History
from historian.inspector import utils


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
            # We can have a SubShell as a parent, we need to `up` it in order to
            # run any cleanup
            if isinstance(self.parent, SubShell):
                self.parent.cmdqueue.append("up")
            # If our parent is a regular `BaseShell` we have reached the root
            # shell and can quit
            else:
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
        super(InspectorShell, self).__init__(*args, **kwargs)
        self.parser_args = pargs
        # TODO: This will need to handle multiple
        self.hist = History(pargs.histories)

    def get_prompt(self):
        pmpt = "historian"
        if self.hist:
            pmpt += " [{}]".format(self.hist.db_path)

        return pmpt + "> "

    def do_load(self, arg):
        self.hist = History(arg)

    def do_unload(self, arg):
        self.hist.close()
        self.hist = None

    def do_db(self, arg):
        if self.hist:
            self.spawn_subshell(DBShell, hist=self.hist)
        else:
            print("[!!] No Loaded DB")

    def do_enter(self, arg):
        self.spawn_subshell(DBShell)

    def postloop(self):
        if self.hist:
            self.hist.close()


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
        if not isinstance(hist, History):
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
        try:
            url = self.hist.get_url_by_id(arg)
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
