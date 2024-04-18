from typing import Union
from dataclasses import dataclass

from sqlalchemy import insert, Engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker

from data.database import DatabasesNames
from data.database import (db_metadata_transactions, db_engine_transactions,
                           db_metadata_portfolios, db_engine_portfolios)
from data.records import StockRecord
from data.database_models import generate_table_by_id_for_selected_database
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

def get_stock_data_from_selected_database_table(database_name: str, table_name: str, stock_data_uid: str):
    """
    Fetches stock record data from a specified table within a given database based on a unique stock data identifier.

    Args:
        database_name (str): The name of the database from which to retrieve the stock data.
        table_name (str): The name of the table within the database where stock data is stored.
        stock_data_uid (str): The unique identifier for the stock data to retrieve.

    Returns:
        StockRecord: An instance of StockRecord containing the retrieved stock data, or None if no data is found.

    Raises:
        ValueError: If the specified database or table cannot be accessed or does not exist.
    """
    try:
        table_format, metadata, engine = get_database_variables_by_name(database_name)
        
        # Create a session to interact with the database
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Access the specific table from metadata
        if table_name not in metadata.tables:
            logger.error(f"Table {table_name} does not exist in database {database_name}")
            return None
        
        table_object = metadata.tables[table_name]
        
        # Create a select query to fetch the stock record by UID
        query = select(table_object).where(table_object.c.uid == stock_data_uid)  # Ensure the column name matches the field name in the dataclass
        
        # Execute the query
        result = session.execute(query).scalar_one_or_none()
        
        # Convert the result to a dictionary if found, and instantiate a StockRecord
        if result:
            return StockRecord.from_dict(dict(result))
        return None
    except Exception as error:
        logger.error(f"Error fetching stock data from {table_name} in {database_name}: {error}")
        return None
    finally:
        session.close()


def move_row_between_databases(from_database_name: str, to_database_name: str, table_name: str, row_id: str, delete_original: bool = False):
    # Retrieve database variables for both source and target databases
    _, metadata_from, engine_from = get_database_variables_by_name(from_database_name)
    table_format_to, metadata_to, engine_to = get_database_variables_by_name(to_database_name)

    if metadata_from is None or engine_from is None or metadata_to is None or engine_to is None:
        logger.error(f"Error retrieving database variables for databases {from_database_name} and {to_database_name}")
        logger.error("Stopping row move")
        return

    # Create sessions for both source and target databases
    Session_from = sessionmaker(bind=engine_from)
    session_from = Session_from()

    try:
        # Fetch the row from the source database
        table_from = metadata_from.tables[table_name]
        query = select(table_from).where(table_from.c.uid == row_id)
        row = session_from.execute(query).fetchone()

        if row:
            # Check if the target table exists, create if not
            if table_name not in metadata_to.tables:
                generate_table_by_id_for_selected_database(table_name, to_database_name)
            
            # Prepare data for insertion by converting the row into a dictionary
            data_to_insert = row

            # Insert the data into the target database
            add_stock_data_to_selected_database_table(to_database_name, table_name, data_to_insert)

            # Optionally delete the original record
            if delete_original:
                delete_stmt = table_from.delete().where(table_from.c.uid == row_id)
                session_from.execute(delete_stmt)
                session_from.commit()
                logger.info(f"Deleted original row with ID {row_id} from {from_database_name}")

            logger.info(f"Successfully moved row with ID {row_id} from {from_database_name} to {to_database_name}")
        else:
            logger.warning(f"No data found with UID {row_id} in {from_database_name}")

    except Exception as error:
        session_from.rollback()
        logger.error(f"Failed to move row: {error}")
    finally:
        session_from.close()

