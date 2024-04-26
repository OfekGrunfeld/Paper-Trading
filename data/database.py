from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from records.database_records import DatabasesNames
from utils.logger_script import logger

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

default_connect_args = {"check_same_thread": False}

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

def initialise_all_databases() -> bool:
    try:
        global db_base_userbase, db_engine_userbase, db_metadata_transactions, db_engine_transactions, db_metadata_portfolios, db_engine_portfolios

        db_base_userbase.metadata.create_all(bind=db_engine_userbase)
        db_metadata_transactions.reflect(bind=db_engine_transactions)
        db_metadata_portfolios.reflect(bind=db_engine_portfolios)
        return True
    except Exception as error:
        logger.critical(f"Error initialising databases. Error: {error}")
        return False
