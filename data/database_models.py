import uuid
from typing import Union, Generator

from sqlalchemy import insert, Column, String, Table, Integer, JSON, Float
from sqlalchemy.orm import Session

from data.database import (db_base_userbase,
                           db_metadata_users_stocks, db_engine_stocksbase, db_metadata_stocksbase, 
                           stocksbase_name, 
                           db_sessionmaker_userbase, db_sessionmaker_users_stocks, db_engine_users_stocks)
from utils.server_protocol import logger

def generate_uuid():
    return str(uuid.uuid4())

class Userbase(db_base_userbase):
    """
    Userbase databse:
    ID: guid | EMAIL: string | USERNAME: string | PASSWORD: string
    """
    __tablename__ = "Userbase"

    id = Column(String, primary_key=True, default=generate_uuid, unique=True)
    
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    def __str__(self) -> str:
        try:
            return f"id: {self.id}, email: {self.email}, username: {self.username}, password: {self.password}"
        except Exception as error:
            return f"Failed creating string: {error}"
    

@staticmethod
def generate_user_stocks_table_by_id(id: str):
    """
    Generate a table of a user to store stocks in
    :param id: A user's GUID
    """
    new_table = Table(
        id,
        db_metadata_users_stocks,
        Column("timestamp", Integer, primary_key=True, unique=True, nullable=False),
        Column("ticker", String),
        Column("action", String),
        Column("amount", Float),
        Column("price", Float),
        extend_existing=True
    )
    new_table.create(db_engine_users_stocks)
    # db_metadata_users_stocks.create_all(db_engine_users_stocks)
    print(db_metadata_users_stocks.tables)

@staticmethod
def add_stock_to_users_stocks_table(id: str, stock_data: dict):
    """
    
    """
    global db_metadata_users_stocks
    # Get user's stocks table reference from the database
    users_stocks_table = get_users_stocks_table_by_name(id)

    # If there was no table found
    if users_stocks_table is None:
        logger.error(f"Could not add user's stocks (id:{id}) table ")
    try:
        insert(users_stocks_table).values(stock_data)
        db: Session = get_db_users_stocks()
        db.commit()
    except Exception as error:
        logger.error(f"Could not add user's stock(s) data to database")
    logger.info(f"Done adding stock data to user {id}'s table")

@staticmethod
def get_users_stocks_table_by_name(name: str) -> Union[Table, None]:
    try:
        users_stocks_table = db_metadata_users_stocks.tables[stocksbase_name]
        return users_stocks_table
    except Exception as error:
        logger.error(f"Could not find table {name} in user's stocks database: {error}")
        return None
    

@staticmethod
def generate_stock_table_for_stocksbase_by_ticker(ticker: str):
    """
    Generate a table for a specific stock in the stocksbase database
    :param ticker: A valid ticker (stock symbol, e.g: AAPL)
    """
    # NOT COMPLETE - ADD VALIDATION FOR STOCKS TICKERS
    possible_tickers = []
    possible_tickers.append(ticker)
    if ticker not in possible_tickers:
        logger.warning("Specified ticker is not valid")
        return 
    
    new_table = Table(
        ticker,
        # db_metadata_stocksbase,
        Column("ticker", String, default=ticker, primary_key=True)
    )
    new_table.create(db_engine_stocksbase)


  
# Get database with generator function
def get_db_userbase() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_userbase()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USERBASE DATABASE: {error}")
    finally:
        db.close()

def get_db_users_stocks() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_users_stocks()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USER'S STOCKS DATABASE: {error}")
    finally:
        db.close()

"""
AAPL = Table(
    "AAPL",
    db_metadata_stocksbase,
    Column("ticker", String, default="AAPL", primary_key=True),
)
BA = Table(
    "BA",
    db_metadata_stocksbase,
    Column("ticker", String, default="BA", primary_key=True),
)
AMZN = Table(
    "AMZN",
    db_metadata_stocksbase,
    Column("ticker", String, default="AAPL", primary_key=True),
)
"""