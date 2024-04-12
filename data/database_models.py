import uuid
from typing import Union, Generator, get_type_hints, Literal
from dataclasses import fields
from datetime import datetime

from sqlalchemy import insert, Column, String, Table, DateTime, Double
from sqlalchemy.orm import Session
import numpy as np

from data.database import (db_base_userbase,
                           db_metadata_transaction_history,
                           db_engine_transaction_history,
                           get_db_userbase, get_db_transaction_history)
from utils.logger_script import logger
from utils.constants import START_BALANCE
from data.stock_record import StockRecord

   
def generate_uuid() -> str:
    return str(uuid.uuid4())

class Userbase(db_base_userbase):
    """
    Userbase databse:
    ID: uuid | EMAIL: string | USERNAME: string | PASSWORD: string
    """
    __tablename__ = "Userbase"

    id = Column(String, primary_key=True, default=generate_uuid, unique=True)
    
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    balance = Column(Double, nullable=False, default=START_BALANCE) # start balance is $100,000

    def __str__(self) -> str:
        try:
            return f"id: {self.id}, email: {self.email}, username: {self.username}, password: {self.password}, balance: {self.balance}"
        except Exception as error:
            return f"Failed creating string: {error}"

    
@staticmethod
def generate_transaction_history_table_by_id(id: str):
    """
    Generate a table of a user to store stocks in
    :param id: A user's UUID
    """
    logger.debug(f"Generating user stocks table for user {id}")
    # Reflect dataclass structure in table schema
    type_hints = get_type_hints(StockRecord)
    dataclass_columns = []
    for field in fields(StockRecord):
        nullable = False
        field_type = type_hints[field.name]
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
        db_metadata_transaction_history,
        *dataclass_columns,
        extend_existing=True
    )
    logger.debug(f"Adding table for user {id}")
    try: 
        new_table.create(db_engine_transaction_history)
        logger.debug(f"Successfully added table to user's stocks database {id}")
    except Exception as error:
        logger.error(f"Error raised while adding table {id} to user's stocks database. Error: {error}")
  
@staticmethod
def add_stock_to_transaction_history_table(id: str, stock_data: dict):
    """
    
    """
    global db_metadata_transaction_history
    # Get user's stocks table reference from the database
    transaction_history_table= get_transaction_history_table_by_name(id)
    if transaction_history_table is None:
        generate_transaction_history_table_by_id(id)
        transaction_history_table = get_transaction_history_table_by_name(id)

    try:
        # Create insert statement for the user stock's data
        stmt = insert(transaction_history_table).values(stock_data)
        # Get the database, execute and commit
        db: Session = next(get_db_transaction_history())
        db.execute(stmt)
        db.commit()
        db.close()
    except Exception as error:
        logger.error(f"Could not add user's stock(s) data to database: {error}")
        db.rollback()
        logger.debug("Rolled back user's stocks database")
        return
    logger.debug(f"Done adding stock data to user {id}'s table")

def get_transaction_history_table_by_name(name: str) -> Union[Table, None]:
    try:
        transaction_history_table = db_metadata_transaction_history.tables[name]
        return transaction_history_table
    except Exception as error:
        logger.error(f"Could not find table {name} in user's stocks database: {error}")
        return None

# # Get database with generator function
# def get_db_userbase() -> Generator[Session, any, None]:
#     try:
#         db = db_sessionmaker_userbase()
#         yield db
#     except Exception as error:
#         logger.critical(f"ERROR IN GETTING USERBASE DATABASE: {error}")
#     finally:
#         db.close()

# def get_db_transaction_history() -> Generator[Session, any, None]:
#     try:
#         db = db_sessionmaker_transaction_history()
#         yield db
#     except Exception as error:
#         logger.critical(f"ERROR IN GETTING USER'S STOCKS DATABASE: {error}")
#     finally:
#         db.close()