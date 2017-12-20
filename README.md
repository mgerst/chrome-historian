Chrome Historian
================
A tool for inspecting chrome histories. Designed for viewing the chrome history for multiple viewers as once.

Installing
----------
Clone the repo and run either of the following commands:

```bash
pip install .
# Or
python setup.py install
```

Basic Usage
-----------
To inspect a user's history in the CLI you can run the following command:

```bash
chrome-historian -d ~/.config/google-chrome/Default/History inspect
```

You can also point historian to a directory containing multiple histories. It will treat the filenames of these
histories as the username the history belongs to.

```bash
chrome-historian -d ~/histories -m merged.db inspect
```

Historian will merge the histories into a single database (specified by `-m`, defaults to a temporary file).

An example session is shown below:

```
historian [merged.db]> db
historian>DB> list
+All Users------+
| ID | Username |
+----+----------+
| 1  | mattg    |
| 2  | other    |
+----+----------+
historian>DB> user 1
historian>DB (mattg)> search url github.com/mgerst/chrome-historian
+Search Results----------------------------------------------------------+----------------------------------+
| ID    | URL                                                            | TITLE                            |
+-------+----------------------------------------------------------------+----------------------------------+
| 58067 | https://github.com/mgerst/chrome-historian                     | mgerst/chrome-historian          |
| 58097 | https://github.com/mgerst/chrome-historian/issues              | Issues * mgerst/chrome-historian |
+-------+----------------------------------------------------------------+----------------------------------+
historian>DB (mattg)> inspect 58067
hist>(mattg)>url 58067> info
+-------------+--------------------------------------------+
| ID          | 58067                                      |
| Url         | https://github.com/mgerst/chrome-historian |
| Title       | Issues * mgerst/chrome-historian           |
| Visit Count | 13                                         |
| Last Visit  | 2017-12-19 04:44:12.183030                 |
| Typed Count | 0                                          |
+-------------+--------------------------------------------+
```

You can even view all the times a url was visited.

```
hist>(mattg)>url 58067> visits
+Visits for URL 58067-----------------+------+------------------------------------+--------+
| ID     | TIME                       | TYPE | FLAGS                              | FROM   |
+--------+----------------------------+------+------------------------------------+--------+
| 254491 | 2017-10-19 23:11:11.872131 | LINK | CHAIN_END|CHAIN_START              | 254490 |
| 254494 | 2017-10-19 23:16:56.743393 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 254497 | 2017-10-19 23:17:02.764693 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 254498 | 2017-10-19 23:17:03.220186 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 254500 | 2017-10-19 23:17:09.259315 | LINK | CHAIN_END|CHAIN_START|FORWARD_BACK | 0      |
| 278854 | 2017-12-19 04:02:10.729247 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 278855 | 2017-12-19 04:02:11.161222 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 278898 | 2017-12-19 04:15:20.734545 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 278899 | 2017-12-19 04:15:21.187774 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 278984 | 2017-12-19 04:43:44.892232 | LINK | CHAIN_END|CHAIN_START              | 278983 |
| 278985 | 2017-12-19 04:43:56.128881 | LINK | CHAIN_END|CHAIN_START              | 0      |
| 278988 | 2017-12-19 04:44:00.286482 | LINK | CHAIN_END|CHAIN_START|FORWARD_BACK | 0      |
| 278992 | 2017-12-19 04:44:12.183030 | LINK | CHAIN_END|CHAIN_START|FORWARD_BACK | 0      |
+--------+----------------------------+------+------------------------------------+--------+
```

Web Interface
-------------
There is also a web interface that can display a graph of the user's browsing for any given url in the history.

```bash
chrome-historian -d ~/histories -m merged.db server
```