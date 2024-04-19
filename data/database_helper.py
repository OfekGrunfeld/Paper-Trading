from typing import Union, List, Tuple, Optional
from collections import Counter

from sqlalchemy import insert, Table, select, delete
from sqlalchemy.orm import sessionmaker

from records.stock_record import StockRecord
from data.database_models import generate_table_by_id_for_selected_database, get_database_variables_by_name, Userbase
from data.query_helper import does_row_exist_in_table, get_user_shares_by_symbol
from utils.logger_script import logger
from encryption.userbase_encryption import encode_username, encode_password

def get_table_object_from_selected_database_by_name(table_name: str, database_name: str) -> Union[Table, None]:
    try:
        _, metadata, engine = get_database_variables_by_name(database_name)
        if metadata is not None:
            table_object = metadata.tables[table_name]
            return table_object
    except Exception as error:
        logger.warning(f"Could not find table {table_name} in {database_name} database: {error}")
        return None

def add_stock_data_to_selected_database_table(database_name: str, table_name: str, stock_data: tuple) -> bool:
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

    uid = stock_data["uid"]

    # Checking if the table exists if not then generate
    while True:
        table_object = get_table_object_from_selected_database_by_name(table_name, database_name)
        if table_object is None:
            logger.error("Table object not found or table does not exist.")
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
        shares_list = get_user_shares_by_symbol(database_name, uuid, symbol)
        for _, shares in shares_list:
            symbol_counts[symbol] += shares

    return list(symbol_counts.items())

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
    
    if not metadata or table_name not in metadata.tables:
        logger.error(f"Table {table_name} does not exist in {database_name}.")
        return False

    table = metadata.tables[table_name]
    session = sessionmaker(bind=engine)()

    try:
        # Create delete statement for the row with the given UID
        delete_stmt = delete(table).where(table.c.uid == uid)
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

def create_user_model(email: Optional[str], username: str, password: str) -> Union[Userbase, None]:
    """
    Creates a new user model by optionally assigning a provided email, and always assigning an encoded username and encoded password.
    Email is optional but username and password are mandatory for user creation.

    Args:
        email (Optional[str]): The email address of the user. It is converted to lowercase before being stored. Can be None.
        username (str): The username of the user. It is encoded using SHA-256 hashing before being stored.
        password (str): The password of the user. It is encoded using MD5 hashing before being stored.

    Returns:
        Userbase or None: Returns a `Userbase` instance initialized with the provided credentials if the required inputs (username and password) are valid.
                          Returns `None` if the required inputs are not provided, indicating incomplete user data.
    """
    if username is None or password is None:
        logger.error("Cannot create a user without a username or password.")
        return None

    user_model = Userbase()

    # Normalize and encode the user credentials
    if email:
        user_model.email = email.lower()  # Normalize email to lowercase

    user_model.username = encode_username(username)
    user_model.password = encode_password(password) 

    return user_model