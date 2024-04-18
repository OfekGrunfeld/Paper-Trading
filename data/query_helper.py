from sqlalchemy import Engine, MetaData, select, and_
from sqlalchemy.orm import sessionmaker

from data.records import StockRecord
from data.database_helper import get_database_variables_by_name
from utils.logger_script import logger

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
                logger.debug(f"All columns to query are in the table")
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
    logger.debug(f"Got a request to query {database_name} with filters: {filters}")
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

def does_row_exist_in_table(database_name: str, table_name: str, row_uid: str) -> bool:
    """
    Check if a row UID exists in a specific table within a database.

    Args:
        database_name (str): The name of the database.
        table_name (str): The name of the table to check.
        uid (str): The UID to check for in the table.

    Returns:
        bool: True if the UID exists, False otherwise.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if table_name not in metadata.tables:
            logger.error(f"Table {table_name} does not exist in database {database_name}")
            return False

        table_object = metadata.tables[table_name]
        exists = session.query(table_object).filter_by(uid=row_uid).scalar() is not None
        return exists
    except Exception as error:
        logger.error(f"Error checking UID existence: {error}")
        return False
    finally:
        session.close()