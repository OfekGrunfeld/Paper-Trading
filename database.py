from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from server_protocol import logger
SQLALCHEMY_USERBASE_URL = "sqlite:///./Userbase.sqlite"

# create engine for userbase
db_engine_userbase = create_engine(
    SQLALCHEMY_USERBASE_URL, connect_args={"check_same_thread": False}
)  

db_session_userbase = sessionmaker(autocommit=False, autoflush=False, bind=db_engine_userbase)

db_base_userbase: declarative_base = declarative_base()



SQLALCHEMY_USERS_STOCKS_URL = "sqlite:///./Users_Stocks.sqlite"

# create engine for userbase
db_engine_users_stocks = create_engine(
    SQLALCHEMY_USERBASE_URL, connect_args={"check_same_thread": False}
)  

db_metadata_users_stocks = MetaData()

SQLALCHEMY_STOCKSBASE_URL = "sqlite:///./Users_Stocks.sqlite"

# create engine for userbase
db_engine_stocksbase = create_engine(
    SQLALCHEMY_STOCKSBASE_URL, connect_args={"check_same_thread": False}
)  

db_metadata_stocksbase = MetaData()
