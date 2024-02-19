from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


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
userbase_name = "Userbase"
db_engine_userbase = create_engine(
    create_database_url(userbase_name), connect_args=default_connect_args
) 
db_sessionmaker_userbase = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_userbase)
db_base_userbase = declarative_base()


# create engine for users stocks database
users_stocks_name = "Users_Stocks"
db_engine_users_stocks = create_engine(
    create_database_url(users_stocks_name), connect_args=default_connect_args
) 
db_sessionmaker_users_stocks = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_users_stocks)
db_metadata_users_stocks = MetaData()

# create engine for stocksbase
stocksbase_name = "Stocksbase"
db_engine_stocksbase = create_engine(
    create_database_url(stocksbase_name), connect_args=default_connect_args 
)  
db_metadata_stocksbase = MetaData()
