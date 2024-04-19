from typing import Union, List, Tuple
from enum import Enum
import numpy as np

from sqlalchemy import Engine, MetaData, select, and_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import operators
from data.database import DatabasesNames, get_db
from data.database_models import Userbase, UserIdentifiers, get_database_variables_by_name
from data.records import StockRecord
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

def get_user_from_userbase(identifier: str, value: str) -> Union[Userbase, None]:
    """
    Fetches a user from the database based on the provided identifier and value,
    excluding the possibility to search by password for security reasons.

    Args:
        identifier (str): The identifier type, which can be 'uuid', 'email', or 'username'.
        value (str): The value corresponding to the identifier.

    Returns:
        Userbase: The Userbase object if found, None otherwise.
    """
    # Disallow searching by password
    if identifier == 'password':
        logger.error("Searching by password is not allowed.")
        return None
    if identifier not in UserIdentifiers:
        logger.error(f"Identifier is not one of the supported identifiers. Chosen identifier: {identifier}.")
        return None

    db_userbase: Session = next(get_db(DatabasesNames.userbase.value))

    try:
        # Dynamically set the attribute to filter on based on the identifier
        filter_condition = getattr(Userbase, identifier) == value
        user_model = db_userbase.query(Userbase).filter(filter_condition).one()
        return user_model
    except NoResultFound:
        logger.info(f"No user found with {identifier} = {value}.")
        return None
    except Exception as error:
        logger.error(f"Error retrieving user from database: {error}")
        return None
    finally:
        db_userbase.close()

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
        import traceback
        logger.error(f"Failed to fetch shares for symbol {symbol} for user {uuid}: {error}")
        print(traceback.format_exc())
        return []
    finally:
        session.close()
