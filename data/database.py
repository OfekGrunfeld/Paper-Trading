from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from utils.server_protocol import logger

@staticmethod
def create_database_url(database_name: str) -> str:
    """
    Generate a database url for sqlite
    :param database_name: Database name
    :returns: Database url E.g sqlite:///./database_name.sqlite
    """
    prefix = "sqlite:///./"
    suffix = ".sqlite"

    database_url = prefix + database_name + suffix

    return database_url

default_connect_args = {"check_same_thread": False}

# create engine for userbase
db_engine_userbase = create_engine(
    create_database_url("Userbase"), connect_args=default_connect_args
)  
db_session_userbase = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_userbase)
db_base_userbase = declarative_base()


# create engine for users stocks database
db_engine_users_stocks = create_engine(
    create_database_url("Users_Stocks"), connect_args=default_connect_args
) 
db_metadata_users_stocks = MetaData()

# create engine for stocksbase
db_engine_stocksbase = create_engine(
    create_database_url("Stocksbase"), connect_args=default_connect_args
)  
db_metadata_stocksbase = MetaData()
