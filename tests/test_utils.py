from datetime import datetime
from historian.utils import webkit_datetime, hash_file, get_dbs


def test_webkit_datetime():
    itime = 13109575048813599
    dtime = webkit_datetime(itime)
    assert dtime == datetime(year=2016, month=6, day=5, hour=4, minute=37, second=28, microsecond=813599)


def test_hash_file(tmpdir):
    testfile = tmpdir.join("test.txt")
    testfile.write("test")
    print(testfile.read())
    assert hash_file(str(testfile)) == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def test_get_dbs(tmpdir):
    user1 = tmpdir.join("user1")
    user1.write("test")
    user2 = tmpdir.join("user2")
    user2.write("test")

    dbs = get_dbs(str(tmpdir))
    assert str(user1) in dbs
    assert str(user2) in dbs
