from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./db1.sqlite"

# create engine for database
db_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)  

db_session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

db_base = declarative_base()
