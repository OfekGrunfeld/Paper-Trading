from typing import Union
from dataclasses import dataclass

from sqlalchemy import insert, Engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

from data.database import DatabasesNames
from data.database import (db_metadata_transactions, db_engine_transactions,
                           db_metadata_portfolios, db_engine_portfolios)
from data.records import StockRecord
from data.query_helper import does_row_exist_in_table
from utils.logger_script import logger

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

def get_table_object_from_selected_database_by_name(table_name: str, database_name: str) -> Union[Table, None]:
    try:
        table_format, metadata, engine = get_database_variables_by_name(database_name)
        if metadata is not None:
            table_object = metadata.tables[table_name]
            return table_object
    except Exception as error:
        logger.warning(f"Could not find table {table_name} in user's stocks database: {error}")
        return None

def add_stock_data_to_selected_database_table(database_name: str, table_name: str, stock_data: tuple):
    """
    Add stock data to a selected database table. It first checks if the UID already exists in the table,
    and if not, it adds the stock data.

    Args:
        database_name (str): The name of the database.
        table_name (str): The name of the table where data is to be added.
        stock_data (dict): The stock data to be inserted into the table.
    """
    uid = stock_data[0]
    if uid is None:
        logger.error("UID is missing from stock data, cannot proceed.")
        return

    # Checking if the UID already exists in the table
    if does_row_exist_in_table(database_name, table_name, uid):
        logger.info(f"UID {uid} already exists in {table_name}. No data added to prevent duplication.")
        return

    # Proceed to add data if UID does not exist
    _, _, engine = get_database_variables_by_name(database_name)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        table_object = get_table_object_from_selected_database_by_name(table_name, database_name)
        if table_object is None:
            logger.error("Table object not found or table does not exist.")
            return

        # Insert the stock data
        stmt = insert(table_object).values(stock_data)
        db.execute(stmt)
        db.commit()
        logger.info(f"Successfully added stock data with UID {uid} to {table_name} in {database_name}.")
    except Exception as error:
        db.rollback()
        logger.error(f"Failed to insert stock data: {error}")
    finally:
        db.close()
