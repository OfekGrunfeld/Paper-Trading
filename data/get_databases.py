from dataclasses import dataclass
from typing import Generator, Union
import traceback

from sqlalchemy import MetaData, Engine, Table
from sqlalchemy.orm import Session

from data.database import (db_sessionmaker_userbase, db_sessionmaker_transactions, db_sessionmaker_portfolios,
                           db_metadata_transactions, db_engine_transactions,
                           db_metadata_portfolios, db_engine_portfolios)
from records.database_records import DatabasesNames
from records.stock_record import StockRecord
from utils.logger_script import logger

# Get databases with generator functions
def get_db_userbase() -> Generator[Session, any, None]:
    try:
        db = db_sessionmaker_userbase()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USERBASE DATABASE: {error}")
        logger.critical(traceback.format_exc())
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
    

def get_database_variables_by_name(database_name: str):
    """
    Retrieves configuration variables for a specified database by its name.

    This function dynamically matches the `database_name` to the corresponding
    SQLAlchemy `Table`, `MetaData`, and `Engine` configurations based on predefined
    database settings. It is designed to facilitate the connection and interaction
    with different database schemas managed within the application.

    Args:
        `database_name` (str): The name of the database for which to retrieve configuration.
                               This should be one of the values specified in `DatabasesNames`.

    Returns:
        tuple: A tuple containing three elements in the order:
               (table_format, metadata, engine)
               - `table_format` (`dataclass`): The dataclass associated with the database tables.
               - `metadata` (`MetaData`): The metadata object associated with the database.
               - `engine` (`Engine`): The database engine object for executing queries.
    """
     
    table_format = None
    metadata = None
    engine = None
    database_name = database_name.lower()

    match(database_name):
        case DatabasesNames.transactions.value:
            table_format: dataclass = StockRecord
            metadata: MetaData = db_metadata_transactions
            engine: Engine = db_engine_transactions
        
        case DatabasesNames.portfolios.value:
            table_format: dataclass = StockRecord
            metadata: MetaData = db_metadata_portfolios
            engine: Engine = db_engine_portfolios
        
        case _:
            logger.error(f"Couldn't find database {database_name} or it is not supported")
            return
    
    return (table_format, metadata, engine)

def get_table_object_from_selected_database_by_name(database_name: str, table_name: str) -> Union[Table, None]:
    try:
        table_object = None
        match(database_name):
            case DatabasesNames.transactions.value:
                table_object = db_metadata_transactions.tables.get(table_name, None)
            case DatabasesNames.portfolios.value:
                table_object = db_metadata_portfolios.tables.get(table_name, None)
            case _:
                logger.error(f"Unsupported database to get a table from ({database_name})")
                return None
        
        if table_object is None:
            logger.warning(f"Failed to find table {table_name} in database {database_name}")
        return table_object
    except Exception as error:
        logger.error(f"Error occured while trying to get table object with name {table_name} from database {database_name}")
        return None
