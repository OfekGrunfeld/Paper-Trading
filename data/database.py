from enum import Enum
from typing import Generator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from utils.logger_script import logger

class DatabasesNames(Enum):
    userbase = "userbase"
    transactions = "transactions"
    portfolios = "portfolios"

    @classmethod
    def __contains__(cls, item):
        return item in (member.value for member in cls)
    

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
db_engine_userbase = create_engine(
    create_database_uri(DatabasesNames.userbase.value), connect_args=default_connect_args
) 
db_sessionmaker_userbase = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_userbase)
db_base_userbase = declarative_base()

# create engine for transactions 
db_engine_transactions = create_engine(
    create_database_uri(DatabasesNames.transactions.value), connect_args=default_connect_args
) 
db_sessionmaker_transactions = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_transactions)
db_metadata_transactions = MetaData()


# create engine for portfolios 
db_engine_portfolios = create_engine(
    create_database_uri(DatabasesNames.portfolios.value), connect_args=default_connect_args
) 
db_sessionmaker_portfolios = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_portfolios)
db_metadata_portfolios = MetaData()


def create_all_databases():
    global db_base_userbase, db_engine_userbase, db_metadata_transactions, db_engine_transactions, db_metadata_portfolios, db_engine_portfolios

    
    db_base_userbase.metadata.create_all(bind=db_engine_userbase)
    db_metadata_transactions.reflect(bind=db_engine_transactions)
    db_metadata_portfolios.reflect(bind=db_engine_portfolios)
# Get databases with generator functions
def get_db_userbase() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_userbase()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USERBASE DATABASE: {error}")
    finally:
        db.close()

def get_db_transactions() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_transactions()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING TRANSACTIONS DATABASE: {error}")
    finally:
        db.close()

def get_db_portfolio() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_portfolios()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING PORTFOLIOS DATABASE: {error}")
    finally:
        db.close()

database_functions = {
    DatabasesNames.userbase.value: get_db_userbase,
    DatabasesNames.transactions.value: get_db_transactions,
    DatabasesNames.portfolios.value: get_db_portfolio,
}

def get_db(database_name: str):
    """
    Unified generator to yield a session for a specified database.
    
    Args:
        database_name (str): The name of the database to yield a session for.

    Yields:
        Session: A database session.
    """
    if database_name in DatabasesNames:
        generator_function = database_functions[database_name]
        yield from generator_function()
    else:
        raise ValueError(f"No database found with the name {database_name}")
