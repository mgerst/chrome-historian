import os


def get_dbs(database):
    return [os.path.join(database, f) for f in os.listdir(database) if os.path.isfile(os.path.join(database, f))]