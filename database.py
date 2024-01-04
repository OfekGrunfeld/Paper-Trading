from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./db1.sqlite"

# create engine for database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)  

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
