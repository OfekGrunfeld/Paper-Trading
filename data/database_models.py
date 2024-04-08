import uuid
from typing import Union, Generator, get_type_hints, Literal, Optional
from dataclasses import fields
from datetime import datetime

from sqlalchemy import insert, Column, String, Table, Integer, Float, DateTime, MetaData, Double
from sqlalchemy.orm import Session
import numpy as np

from data.database import (db_base_userbase,
                           db_metadata_users_stocks,
                           users_stocks_name,
                           db_sessionmaker_userbase, db_sessionmaker_users_stocks, db_engine_users_stocks)
from utils.logger_script import logger
from data.stock_record import StockRecord





def generate_uuid() -> str:
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
    :param id: A user's UUID
    """
    # Reflect dataclass structure in table schema
    type_hints = get_type_hints(StockRecord)
    dataclass_columns = []
    for field in fields(StockRecord):
        nullable = False
        field_type = type_hints[field.name]
        print(field_type)
        if field_type == str:
            column_type = String 
        elif field_type == datetime:
            column_type = DateTime
        elif field_type == float or field_type == np.float64:
            column_type = Double
        elif hasattr(field_type, '__origin__'):  
            if field_type.__origin__ is Literal:
                column_type = String
            elif field_type.__origin__ is Union and type(None) in field_type.__args__: # check for Optional
                column_type = String
                nullable = True 
        else:
            continue  # Skip fields with unhandled types

        dataclass_columns.append(Column(field.name, column_type, nullable=nullable))


    new_table = Table(
        id,
        db_metadata_users_stocks,
        *dataclass_columns,
        extend_existing=True
    )
    logger.debug(f"Adding table for user {id}")
    try: 
        new_table.create(db_engine_users_stocks)
        logger.debug(f"Successfully added table to user's stocks database {id}")
    except Exception as error:
        logger.error(f"Error raised while adding table {id} to user's stocks database: {error}")

    
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
        # Create insert statement for the user stock's data
        stmt = insert(users_stocks_table).values(stock_data)
        # Get the database, execute and commit
        db: Session = next(get_db_users_stocks())
        db.execute(stmt)
        db.commit()
        db.close()
    except Exception as error:
        logger.error(f"Could not add user's stock(s) data to database: {error}")
        db.rollback()
        logger.debug("Rolled back user's stocks database")
        return
    logger.debug(f"Done adding stock data to user {id}'s table")

@staticmethod
def get_users_stocks_table_by_name(name: str) -> Union[Table, None]:
    try:
        users_stocks_table = db_metadata_users_stocks.tables[name]
        return users_stocks_table
    except Exception as error:
        logger.error(f"Could not find table {name} in user's stocks database: {error}")
        return None
    

# @staticmethod
# def generate_stock_table_for_stocksbase_by_ticker(ticker: str):
#     """
#     Generate a table for a specific stock in the stocksbase database
#     :param ticker: A valid ticker (stock symbol, e.g: AAPL)
#     """
#     # NOT COMPLETE - ADD VALIDATION FOR STOCKS TICKERS
#     possible_tickers = []
#     possible_tickers.append(ticker)
#     if ticker not in possible_tickers:
#         logger.warning("Specified ticker is not valid")
#         return 
    
#     new_table = Table(
#         ticker,
#         # db_metadata_stocksbase,
#         Column("ticker", String, default=ticker, primary_key=True)
#     )
#     new_table.create(db_engine_stocksbase)


  
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