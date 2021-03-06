import datetime
import hashlib
import os
from typing import List

BUF_SIZE = 65536


def get_dbs(database: str) -> List[str]:
    """
    Get list of dbs.

    :param database: The database directory
    """
    return [os.path.join(database, f) for f in os.listdir(database) if os.path.isfile(os.path.join(database, f))]


def hash_file(filename: str) -> str:
    """
    Get the hash of a file.

    :param filename: The file to hash
    :return: The hash of the file
    """
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as fp:
        while True:
            data = fp.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def webkit_datetime(itime: int) -> datetime.datetime:
    """
    Convert WebKit's timestamp and convert it to a datetime.

    :param itime: The timestamp in WebKit's format (since 01-Jul-1601)
    :return: UTC datetime
    """
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=itime)
