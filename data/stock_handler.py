from typing import Union
import sched
import time

from sqlalchemy import create_engine, MetaData, Engine, and_
from sqlalchemy.sql import select, operators
from sqlalchemy.orm import sessionmaker

from data.database import DatabasesNames
from data.database_models import get_database_variables_by_name
from utils.logger_script import logger
from data.records import StockRecord

def query_all_tables_in_selected_database(database_name: str, columns: list[str], filters: list[tuple]):
    _, metadata, engine = get_database_variables_by_name(database_name)
    metadata: MetaData
    engine: Engine

    session = sessionmaker(bind=engine)()
    try:
        results = []
        for table_name in metadata.tables:
            table = metadata.tables[table_name]
            if all(col in table.columns for col in columns):
                logger.debug(f"All columns to query ({columns}) are in the table")
                select_columns = [table.c[col] for col in columns]
                query = select(*select_columns)
                
                if filters and all(col in table.columns for col, _, _ in filters):
                    conditions = [op(table.c[col], val) for col, op, val in filters]
                    query = query.where(and_(*conditions))
                
                result = session.execute(query).fetchall()
                results.append([table_name, result])
        return results
    except Exception as error:
        logger.error(f"Error occured while querying for {columns}")
    finally:
        session.close()

def query_all_tables_in_selected_database_for_stock_data(database_name: str, filters: list[tuple]):
    """
    Queries all tables within the specified database, applying given filters, 
    and retrieves stock data as StockRecord instances.

    Args:
        database_name (str): The name of the database to query.
        filters (list[tuple]): A list of tuples where each tuple contains the column name, 
                               the operator, and the value to filter by, e.g., ('status', operators.eq, 'pending').

    Returns:
        list: A list of tuples where each tuple contains a table name and a list of StockRecord instances.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    session = sessionmaker(bind=engine)()
    results = []
    
    try:
        metadata.reflect(bind=engine)
        for table_name in metadata.tables:
            table = metadata.tables[table_name]
            if all(col in table.columns for col, _, _ in filters):
                query = select(table)  # Select all columns from the table

                if filters:
                    conditions = [op(table.c[col], val) for col, op, val in filters]
                    query = query.where(and_(*conditions))

                raw_result = session.execute(query).fetchall()
                
                # Convert each row to a StockRecord instance
                stock_records = [StockRecord.from_tuple(row) for row in raw_result]
                results.append((table_name, stock_records))

        return results
    except Exception as error:
        logger.error(f"Error occurred while querying for stock data in {database_name}: {error}")
        return None
    finally:
        session.close()

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

class StockHandler:
    CHECK_TIME = 15 # seconds
    pending = []

def query_pending_stock_records(scheduler: sched.scheduler):    
    # schedule the next call first
    scheduler.enter(StockHandler.CHECK_TIME, 1, query_pending_stock_records, (scheduler,))
    # Example of using different operators with new filters parameter
    pending_transactions = query_all_tables_in_selected_database_for_stock_data(
        database_name=DatabasesNames.transactions.value,
        filters=[
            ('status', operators.eq, 'pending')
        ],
    )
    StockHandler.pending = pending_transactions
    
    print("Database Results:")
    for table_name, records in pending_transactions:
        print(f"Data from {table_name}:")
        for record in records:
            print(record)

def change_pending(scheduler: sched.scheduler):
    pass

def run_query_loop():
    my_scheduler = sched.scheduler(time.monotonic, time.sleep)
    my_scheduler.enter(StockHandler.CHECK_TIME, 1, query_pending_stock_records, (my_scheduler,))
    # my_scheduler.enter(StockHandler.CHECK_TIME, 2, printer, (my_scheduler,))
    my_scheduler.run()


