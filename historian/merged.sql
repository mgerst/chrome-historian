-- This file describes the merged history database
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE,
  hash TEXT NULL
);
CREATE TABLE urls (
  user_id INTEGER,
  id INTEGER,
  url TEXT,
  title TEXT,
  visit_count INTEGER,
  typed_count INTEGER,
  last_visit_time INTEGER,
  hidden INTEGER,
  favicon_id INTEGER,
  PRIMARY KEY(user_id, id)
);
CREATE TABLE visits (
  user_id INTEGER,
  id INTEGER,
  url INTEGER,
  visit_time INTEGER,
  from_visit INTEGER,
  transition INTEGER,
  segment_id INTEGER,
  visit_duration INTEGER,
  PRIMARY KEY(user_id, id)
);
CREATE TABLE visit_source (
  user_id INTEGER,
  id INTEGER,
  source INTEGER,
  PRIMARY KEY(user_id, id)
);