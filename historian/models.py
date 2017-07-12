from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:////home/matt2/projects/chrome-historian/db.sqlite3', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)


class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, autoincrement=True)
    local_id = Column(Integer, index=True)
    url = Column(String)
    title = Column(String)
    visit_count = Column(Integer)
    typed_count = Column(Integer)
    last_visit_time = Column(BigInteger)
    hidden = Column(Integer)
    favicon_id = Column(Integer)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(
        User,
        backref=backref('urls', uselist=True, cascade='delete,all')
    )

    __table_args__ = (
        UniqueConstraint('id', 'local_id', name='_id_local_id_unique'),
        UniqueConstraint('user_id', 'url', name='_user_url_unique'),
    )


class Visit(Base):
    __tablename__ = 'visits'
    id = Column(Integer, primary_key=True, autoincrement=True)
    local_id = Column(Integer, index=True)

    url_id = Column(Integer, ForeignKey('urls.id'))
    url = relationship(
        Url,
        backref=backref('visits', uselist=True, cascade='delete,all'),
    )

    visit_time = Column(BigInteger)
    from_visit_id = Column(Integer, ForeignKey('visits.id'))
    from_visit = relationship(
        'Visit',
        backref=backref('to_visit', remote_side=[id]),
    )

    transition = Column(Integer)
    segment_id = Column(Integer)
    visit_duration = Column(BigInteger)
