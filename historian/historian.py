import os
from argparse import ArgumentParser
from pathlib import Path

from historian.flask import app
from historian.inspector import InspectorShell
from historian.history import MultiUserHistory, History
from historian.models import Base
from historian.utils import get_dbs


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--histories', help='The location of the chrome history files. Defaults to "histories" in'
                        ' the current directory')
    parser.add_argument('-m', '--merged', help='Location of the merged history DB', default=None)
    parser.add_argument('-c', '--clean-db', help='Clean merged DB', action='store_true', default=False)
    subparsers = parser.add_subparsers()

    webapp = subparsers.add_parser('server', help='Run local web version of historian')
    webapp.set_defaults(func=run_webapp)
    webapp.add_argument('-l', '--host', default='127.0.0.1')
    webapp.add_argument('-p', '--port', default=5000)
    webapp.add_argument('--debug', action='store_true', default=False)

    inspector = subparsers.add_parser('inspect', help='Inspect a chrome history from the command line')
    inspector.set_defaults(func=run_inspector)

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_usage()


def run_webapp(args):
    if args.histories:
        histories = args.histories
    else:
        histories = os.getcwd()

    if args.clean_db and args.merged:
        if os.path.exists(args.merged):
            print("[Historian] Remove old merged DB")
            os.unlink(args.merged)

    history_path = Path(histories)

    if history_path.is_dir():
        dbs = get_dbs(histories)

        print("[Historian] Using histories from {}".format(histories))
        hist = MultiUserHistory(dbs, args.merged)
    else:
        print("[Historian] Using history {}".format(histories))
        hist = History(histories)
    Base.query = hist.db_session.query_property()
    app.config['HISTORIES'] = hist
    app.run(host=args.host, port=args.port, debug=args.debug)


def run_inspector(args):
    InspectorShell(args).cmdloop()
