import json
from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Table, Time, Text
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, connect_args={"options": "-c timezone=utc"})


@contextmanager
def session():
    connection = engine.connect()
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
    try:
        yield db_session
    except Exception as e:
        print(e)
    finally:
        db_session.remove()
        connection.close()


class Employees(Base):
    __tablename__ = 'employees'
    id = Column(Integer, unique=True, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(120))
    first_name = Column(String(120))
    last_name = Column(String(120))
    list_groups_product = Column(String(500))

    def __init__(self, telegram_id, username, first_name, last_name):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    @property
    def get_list_groups_product(self):
        if self.list_groups_product:
            return json.loads(self.list_groups_product)

    def set_list_groups_product(self, list_groups_product):
        self.list_groups_product = json.dumps(list_groups_product)




Base.metadata.create_all(engine)