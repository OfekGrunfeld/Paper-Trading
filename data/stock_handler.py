from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from data.database_models import get_database_variables_by_name, generate_table_by_id_for_selected_database
from data.records import StockRecord
from data.database_helper import add_stock_data_to_selected_database_table
from utils.logger_script import logger
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

# class StockHandler:
#     CHECK_TIME = 15 # seconds
#     pending = []

# def change_pending(scheduler: sched.scheduler):
#     pass

# def run_query_loop():
#     my_scheduler = sched.scheduler(time.monotonic, time.sleep)
#     my_scheduler.enter(StockHandler.CHECK_TIME, 1, query_pending_stock_records, (my_scheduler,))
#     # my_scheduler.enter(StockHandler.CHECK_TIME, 2, printer, (my_scheduler,))
#     my_scheduler.run()


