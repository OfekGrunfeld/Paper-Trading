from typing import Generator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from utils.logger_script import logger

@staticmethod
def create_database_uri(database_name: str) -> str:
    """
    Generate a database uri for sqlite
    :param database_name: Database name
    :returns: Database uri E.g sqlite:///./database_name.sqlite
    """
    prefix = "sqlite:///./"
    suffix = ".sqlite"

    database_uri= f"{prefix}{database_name}{suffix}"

    return database_uri

default_connect_args= {"check_same_thread": False}

# create engine for userbase
userbase_name = "Userbase"
db_engine_userbase = create_engine(
    create_database_uri(userbase_name), connect_args=default_connect_args
) 
db_sessionmaker_userbase = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_userbase)
db_base_userbase = declarative_base()

# create engine for users stocks database
users_stocks_name = "Users_Stocks"
db_engine_users_stocks = create_engine(
    create_database_uri(users_stocks_name), connect_args=default_connect_args
) 
db_sessionmaker_users_stocks = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_users_stocks)
db_metadata_users_stocks = MetaData()

# Get database with generator function
def get_db_userbase() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_userbase()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USERBASE DATABASE: {error}")
    finally:
        db.close()

def get_db_users_stock() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_users_stocks()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USER'S STOCKS DATABASE: {error}")
    finally:
        db.close()

