import hashlib
import os

BUF_SIZE = 65536


def get_dbs(database):
    return [os.path.join(database, f) for f in os.listdir(database) if os.path.isfile(os.path.join(database, f))]


def hash_file(filename: str) -> str:
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as fp:
        while True:
            data = fp.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()
