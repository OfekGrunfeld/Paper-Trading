import uuid

from sqlalchemy import Column, String, Table, Integer
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from server import db_base_userbase
from data.database import (db_metadata_users_stocks, db_metadata_stocksbase, db_engine_stocksbase)
from utils.server_protocol import logger

# "quick fix for uuid"
# i have no clue how this works 
class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value
        
class Userbase(db_base_userbase):
    """
    Userbase databse:
    ID: guid | EMAIL: string | USERNAME: string | PASSWORD: string
    """
    __tablename__ = "Userbase"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True)
    
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    def __str__(self) -> str:
        try:
            return f"id: {self.id}, email: {self.email}, username: {self.username}, password: {self.password}"
        except Exception as error:
            return f"Failed creating string: {error}"

# Not completed
class Users_Stocks():
    """
    Users Stocks database
    ID: guid | ???
    """
    __tablename__ = "Users_Stocks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True)

    def __str__(self) -> str:
        try:
            return None
        except Exception as error:
            return f"Failed creating string: {error}"

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
        db_metadata_stocksbase,
        Column("ticker", String, default=ticker, primary_key=True)
    )
    new_table.create(db_engine_stocksbase)
        
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

