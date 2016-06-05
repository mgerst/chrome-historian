from argparse import ArgumentParser

from historian import app


def main():
    parser = ArgumentParser()
    parser.add_argument('--server', action='store_true', 
            help='Run a web interface')

    args = parser.parse_args()

    if args.server:
        app.app.run()
