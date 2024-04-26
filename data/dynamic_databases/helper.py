from typing import Union, List, Tuple, Sequence, Any
from datetime import datetime
from collections import Counter

import numpy as np
from sqlalchemy import insert, Table, select, delete, MetaData, Engine, and_, inspect, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine.row import Row

from utils.logger_script import logger
from data.dynamic_databases.models import generate_table_by_id_for_selected_database, get_database_variables_by_name
from records.stock_record import StockRecord
from records.database_records import DatabasesNames


def query_all_tables_in_selected_database(database_name: str, columns: list[str], filters: list[tuple]) -> list:
    """
    Query all tables in the selected database based on specified columns and filters.

    Parameters:
        database_name (str): The name of the database to query.
        columns (list[str]): A list of column names to retrieve from each table.
        filters (list[tuple]): A list of tuples specifying filters to apply to the query.
            Each tuple should contain (column_name, operator, value).

    Returns:
        list: A list of tuples containing the table name and corresponding query results.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.error(f"Table {table_name} does not exist in {database_name}.")
        return []
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
        logger.error(f"Error occurred while querying for {columns}: {error}")
        return []
    finally:
        session.close()

def query_all_tables_in_selected_database_for_stock_data(database_name: str, filters: list[tuple]) -> list[StockRecord]:
    """
    Queries all tables within the specified database, applying given filters, 
    and retrieves stock data as StockRecord instances (The whole row)

    Args:
        database_name (str): The name of the database to query.
        filters (list[tuple]): A list of tuples where each tuple contains the column name, 
                               the operator, and the value to filter by, e.g., ('status', operators.eq, 'pending').

    Returns:
        list: A list of tuples where each tuple contains a table name and a list of StockRecord instances.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.error(f"Table {table_name} does not exist in {database_name}.")
    
    session = sessionmaker(bind=engine)()
    results = []
    
    try:
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

def query_specific_columns_from_database_table(database_name: str, table_name: str, columns: list[str] = None) -> Union[StockRecord, Sequence[Row[Any]], None]:
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.error(f"Table {table_name} does not exist in {database_name}.")
        return []
        
    table_object = metadata.tables.get(table_name)
    if table_object is None:
        logger.error(f"Could not retrieve {table_name} from {database_name}.")
        return None

    # If received no columns - treat as special case where you choose all columns except the uid
    if columns is None:
        # Fetch column names directly from the table object
        columns = [column.name for column in inspect(table_object).columns]
        # Remove the 'uid' column if it exists
        columns.remove("uid")

    logger.warning(f"{columns}")

    session = Session(bind=engine)
    try:
        # Build the query selecting only the specified columns
        query = select(*[table_object.c[column] for column in columns])
        logger.warning(f"{query}")
        result = session.execute(query).fetchall()
        logger.warning(f"{result}")
    except Exception as error:
        logger.error(f"Exception occurred. Error: {error}")
        result = None
    finally:
        session.close()

    if columns is None:
        return [StockRecord.from_uidless_tuple(row) for row in result]
    else:
        return result


def remove_row_by_uid(database_name: str, table_name: str, uid: str) -> bool:
    """
    Removes a row identified by UID from the specified table in the specified database.

    Args:
        database_name (str): The name of the database containing the table.
        table_name (str): The name of the table from which the row will be deleted.
        uid (str): The unique identifier of the row to be removed.

    Returns:
        bool: True if the row was successfully deleted, False otherwise.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None:
        logger.error(f"Table {table_name} does not exist in {database_name}.")
        return False

    table_object = metadata.tables.get(table_name, None)
    if table_object is None:
        logger.error(f"Table {table_name} was not found in {database_name}")
        return None

    session = sessionmaker(bind=engine)()

    try:
        # Create delete statement for the row with the given UID
        delete_stmt = delete(table_object).where(table_object.c.uid == uid)
        result = session.execute(delete_stmt)
        session.commit()

        if result.rowcount:
            logger.debug(f"Successfully deleted row with UID {uid} from {table_name}.")
            return True
        else:
            logger.warning(f"No row with UID {uid} found in {table_name}.")
            return False
    except Exception as error:
        session.rollback()
        logger.error(f"Failed to delete row with UID {uid} from {table_name}: {error}")
        return False
    finally:
        session.close()

def move_row_between_databases(from_database_name: str, to_database_name: str, table_name: str, row_id: str, delete_original: bool = False) -> bool:
    _, metadata_from, engine_from = get_database_variables_by_name(from_database_name)
    _, metadata_to, engine_to = get_database_variables_by_name(to_database_name)

    if metadata_from is None or engine_from is None or metadata_to is None or engine_to is None:
        logger.error(f"Error retrieving database variables for databases {from_database_name} and {to_database_name}")
        logger.error("Stopping row move")
        return False

    # Create sessions for both source and target databases
    session_from: Session = sessionmaker(bind=engine_from)

    try:
        # Fetch the row from the source database
        table_object_from = metadata_from.tables.get(table_name, None)
        if table_object_from is None:
            logger.error(f"Table {table_name} was not found in {from_database_name}")
            return None
        query = select(table_object_from).where(table_object_from.c.uid == row_id)
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
                delete_stmt = table_object_from.delete().where(table_object_from.c.uid == row_id)
                session_from.execute(delete_stmt)
                session_from.commit()
                logger.info(f"Deleted original row with ID {row_id} from {from_database_name}")

            logger.info(f"Successfully moved row with ID {row_id} from {from_database_name} to {to_database_name}")
        else:
            logger.warning(f"No data found with UID {row_id} in {from_database_name}")

    except Exception as error:
        session_from.rollback()
        logger.error(f"Failed to move row. Error: {error}")
    finally:
        session_from.close()

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

        table_object: Table = metadata.tables.get(table_name, None)
        exists = session.query(table_object).filter_by(uid=row_uid).scalar() is not None
        return exists
    except Exception as error:
        logger.error(f"Error checking UID existence: {error}")
        return False
    finally:
        session.close()


def get_stock_data_from_selected_database_table(database_name: str, table_name: str, stock_data_uid: str) -> Union[StockRecord, None]:
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
        _, metadata, engine = get_database_variables_by_name(database_name)
        if metadata is None:
            logger.error(f"Error retrieving database variables for databases {database_name}")
            return None

        
        # Create a session to interact with the database
        session = sessionmaker(bind=engine)
        
        # Access the specific table from metadata
        table_object = metadata.tables.get(table_name, None)
        if table_object is None:
            logger.error(f"Table {table_name} was not found in {database_name}")
            return None

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

def add_stock_data_to_selected_database_table(database_name: str, table_name: str, stock_data: dict) -> bool:
    """
    Add stock data to a selected database table. It first checks if the UID already exists in the table,
    and if not, it adds the stock data.

    Args:
        database_name (str): The name of the database.
        table_name (str): The name of the table where data is to be added.
        stock_data (dict): The stock data to be inserted into the table.
    
    Returns:
        bool: Success of the operation:
            `True` if the stock data was added successfully
            `False` if the stock data was not added
    """
    # Get Metadata in order to get the table object
    _, metadata, _ = get_database_variables_by_name(database_name)
    if metadata is None:
        logger.error(f"Error retrieving database variables for databases {database_name}")
        return False
    
    uid = stock_data.get("uid", None)
    if uid is None:
        logger.error("UID not found in stock data.")
        return False

    # Checking if the table exists if not then generate
    while True:
        table_object = metadata.tables.get(table_name, None)
        if table_object is None:
            logger.warning(f"Table {table_name} was not found in {database_name}")
            generate_table_by_id_for_selected_database(database_name=database_name, uuid=table_name)
        else:
            break
    # Checking if the UID already exists in the table
    if does_row_exist_in_table(database_name, table_name, uid):
        logger.info(f"UID {uid} already exists in {table_name}. No data added to prevent duplication.")
        return False

    # Proceed to add data if UID does not exist
    _, _, engine = get_database_variables_by_name(database_name)
    Session = sessionmaker(bind=engine)
    db = Session()

    flag = False
    try:
        

        # Insert the stock data
        stmt = insert(table_object).values(stock_data)
        db.execute(stmt)
        db.commit()
        logger.debug(f"Successfully added stock data with UID {uid} to {table_name} in {database_name}.")
        flag = True
    except Exception as error:
        db.rollback()
        logger.error(f"Failed to insert stock data: {error}")
        flag = False
    finally:
        db.close()
        return flag


# I don't understand why this function is neccessary
# Duplicate of get_owned_user_shares_by_symbol
def get_user_shares_by_symbol(database_name: str, uuid: str, symbol: str) -> List[Tuple[str, float]]:
    """
    Retrieves all share quantities a user has for a given symbol, filtering only 'buy' transactions.

    Args:
        database_name (str): The name of the database where the stock records are stored.
        user_uuid (str): The UUID of the user whose shares are to be queried.
        symbol (str): The stock symbol to filter the shares by.

    Returns:
        List[Tuple[str, float]]: A list of tuples, where each tuple contains the uid of the transaction,
                                 the number of shares and the cost per share.
    """
    # Retrieve database variables
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.warning(f"Database setup not found for {database_name}")
        return []

    # Create a session
    session = Session(bind=engine)

    try:
        table = metadata.tables.get(uuid)
        if table is None:
            logger.warning(f"No table found for user {uuid} in database {database_name}")
            return []

        # Prepare the query with filters
        query = select(table.c.uid, table.c.shares, table.c.cost_per_share).where(
            (table.c.symbol == symbol.upper()) & (table.c.side == "buy")
        )
        results = session.execute(query).fetchall()

        # Convert results to list of tuples (uid, shares)
        shares_list = [(uid, np.double(shares), np.double(cost_per_share)) for uid, shares, cost_per_share in results]
        return shares_list

    except Exception as error:
        logger.error(f"Failed to fetch shares for symbol {symbol} for user {uuid}: {error}")
        return []
    finally:
        session.close()

# I don't understand why this function is neccessary
# Duplicate of get_user_shares_by_symbol
def get_owned_user_shares_by_symbol(database_name: str, uuid: str, symbol: str) -> list:
    """
    Retrieves all share quantities a user has for a given symbol, filtering only 'buy' transactions,
    and includes the transaction timestamp.

    Args:
        database_name (str): The name of the database where the stock records are stored.
        uuid (str): The UUID of the user whose shares are to be queried.
        symbol (str): The stock symbol to filter the shares by.

    Returns:
        dict: A dictionary with transaction details including uid, shares, cost per share, and timestamp.
    """
    # Retrieve database variables
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.warning(f"Database setup not found for {database_name}")
        return {}

    # Create a session
    session = Session(bind=engine)

    try:
        table = metadata.tables.get(uuid)
        if table is None:
            logger.warning(f"No table found for user {uuid} in database {database_name}")
            return {}

        # Prepare the query with filters
        query = select(
            table.c.timestamp, 
            table.c.shares, 
            table.c.cost_per_share, 
        ).where(
            (table.c.symbol == symbol.upper()) & (table.c.side == "buy")
        )
        results = session.execute(query).fetchall()

        # Convert results to a dictionary
        shares_dict: list[dict[str, Union[datetime, np.double]]] = [
            {"timestamp": timestamp, "shares": np.double(shares), "cost_per_share": np.double(cost_per_share), }
            for timestamp, shares, cost_per_share in results
        ]
        
        return shares_dict

    except Exception as error:
        logger.error(f"Failed to fetch shares for symbol {symbol} for user {uuid}: {error}")
        return {}
    finally:
        session.close()

def get_all_symbols_count(database_name: str, uuid: str, symbols: List[str]) -> List[Tuple[str, int]]:
    """
    Retrieves the count of shares for each symbol a user has, summing up all buy transactions.

    Args:
        database_name (str): The name of the database where the stock records are stored.
        uuid (str): The UUID of the user whose shares are to be queried.
        symbols (List[str]): A list of symbols to query for.

    Returns:
        List[Tuple[str, int]]: A list of tuples, each containing a symbol and the total count of shares for that symbol.
        Ensures all queried symbols are returned with a count, defaulting to 0 if no shares are found.
    """
    # Initialize all symbols with a count of 0 to ensure all are included in the output
    symbol_counts = Counter({symbol: 0 for symbol in symbols})

    for symbol in symbols:
        shares_list = get_owned_user_shares_by_symbol(database_name, uuid, symbol)
        for _, shares in shares_list:
            symbol_counts[symbol] += shares

    return list(symbol_counts.items())

def get_unique_symbols_owned(database_name: str, uuid: str):
    """
    Retrieves all owned* unique stock symbols for a user from the database. 
    * Currently owned means that the side in the portfolio database is "buy"
    Args:
        database_name (str): The name of the database.
        uuid (str): The UUID of the user.

    Returns:
        list: A list of unique stock symbols.
    """
    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.warning(f"Database setup not found for {database_name}")
        return []

    session = Session(bind=engine)

    try:
        table = metadata.tables.get(uuid)
        if table is None:
            logger.warning(f"No table found for user {uuid} in database {database_name}")
            return []

        query = select(table.c.symbol.distinct()).where(table.c.side == "buy")
        results = session.execute(query).fetchall()
        
        symbols = [row.symbol for row in results]
        return symbols

    except Exception as error:
        logger.error(f"Failed to fetch unique symbols for user {uuid}: {error}")
        return []
    finally:
        session.close()

# Function that serves a greater purpose than it is actually used for 
# And has bad logic overall - it is only used for one case
def get_summary(database_name: str, table_name: str):
    """
    Retrieves a summary of all unique symbols the user has in both 'buy' and 'sell' sides,
    along with the total share count for each symbol.

    Args:
        database_name (str): The name of the database where the stock records are stored.
        uuid (str): The UUID of the user whose portfolio is to be queried.

    Returns:
        dict: A dictionary with keys 'buy' and 'sell', each containing a dictionary
              of symbols and their corresponding total share count.
    """
    summary = {'buy': {}, 'sell': {}}

    _, metadata, engine = get_database_variables_by_name(database_name)
    if metadata is None or engine is None:
        logger.error(f"Failed to retrieve database settings for {database_name}.")
        return {}

    session = sessionmaker(bind=engine)()

    try:
        table = metadata.tables.get(table_name)
        if table is None:
            logger.error(f"No table found for user {table_name} in database {database_name}.")
            return summary

        for side in summary.keys():
            # Correctly constructing the select statement
            query = select(
                table.c.symbol, 
                func.sum(table.c.shares).label("shares")
            ).where(
                table.c.side == side
            ).group_by(
                table.c.symbol
            )
            results = session.execute(query).fetchall()

            # Populate the summary dictionary
            for symbol, total_shares in results:
                summary[side][symbol] = total_shares
        
        # Portfolios database currently only keeps the owned stocks a user has
        if database_name == DatabasesNames.portfolios.value:
            summary["owned"] = summary["buy"]
            del summary["buy"]
            del summary["sell"]
        return summary
    except Exception as error:
        logger.error(f"Error occurred while querying the portfolio for {table_name}: {error}")
        summary = None
    finally:
        session.close()
        return summary

def compile_user_portfolio(database_name: str, uuid: str) -> dict[str, list[dict[str, Union[datetime, np.double]]]]:
    """
    Compiles a portfolio summary for the user across all their stock symbols.

    Args:
        database_name (str): The name of the database.
        uuid (str): The UUID of the user.

    Returns:
        dict: A dictionary containing all transaction details by stock symbol.
    """
    symbols = get_unique_symbols_owned(database_name, uuid)
    portfolio_summary = {}

    for symbol in symbols:
        portfolio_summary[symbol] = get_owned_user_shares_by_symbol(database_name, uuid, symbol)

    return portfolio_summary
