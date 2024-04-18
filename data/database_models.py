import uuid
from enum import Enum
from typing import Union, get_type_hints, Literal
from dataclasses import fields
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import insert, Column, String, Table, DateTime, Double, Engine, MetaData
from sqlalchemy.orm import Session
import numpy as np

from data.database import (db_base_userbase,
                           db_metadata_transactions, db_engine_transactions,
                           db_metadata_portfolios, db_engine_portfolios,
                           get_db,
                           DatabasesNames)
from utils.logger_script import logger
from utils.constants import START_BALANCE
from data.records import StockRecord

def generate_uuid() -> str:
    """
    Generatea a unique user identifier
    """
    return str(uuid.uuid4())

class Userbase(db_base_userbase):
    """
    Userbase databse:
    uuid: uuid | EMAIL: string | USERNAME: string | PASSWORD: string
    """
    __tablename__ = "userbase"

    uuid = Column(String, primary_key=True, default=generate_uuid, unique=True)
    
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    balance = Column(Double, nullable=False, default=int(START_BALANCE)) 

    def __str__(self) -> str:
        try:
            return f"uuid: {self.uuid}, email: {self.email}, username: {self.username}, password: {self.password}, balance: {self.balance}"
        except Exception as error:
            return f"Failed creating string: {error}"

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

def generate_table_by_id_for_selected_database(uuid: str, database_name: str):
    table_format, metadata, engine = get_database_variables_by_name(database_name)
    
    if table_format is not None and metadata is not None and engine is not None:
        _generate_table_by_id_for_selected_database(
            uuid=uuid, 
            database_name=database_name,
            table_format=table_format, 
            metadata=metadata, 
            engine=engine
        )
    else:
        logger.warning(f"Could not start to generate table for {database_name}. table format, metadata or engine may be invalid.")

def _generate_table_by_id_for_selected_database(uuid: str, database_name: str, table_format: dataclass, metadata: MetaData, engine: Engine):
    """
    Generate a table of a user to store stocks in
    :param uuid: A user's UUID
    """
    if database_name not in DatabasesNames:
        logger.error(f"Cannot generate table for database {database_name} because it is not one of the supported databases")
        return

    logger.info(f"Generating {database_name} table for user {uuid}")

    
    # Reflect dataclass structure in table schema
    type_hints = get_type_hints(table_format)
    dataclass_columns = []
    try:
        for field in fields(StockRecord):
            if field.name.lower() == "uid":
                dataclass_columns.append(Column("uid", String, primary_key=True, unique=True, default=generate_uuid))
                continue
            nullable = False
            field_type = type_hints[field.name]
            if field_type == str:
                column_type = String 
            elif field_type == datetime:
                column_type = DateTime
            elif field_type == float or field_type == np.float64:
                column_type = Double
            elif hasattr(field_type, '__origin__'):  
                if field_type.__origin__ is Literal:
                    column_type = String
                elif field_type.__origin__ is Union and type(None) in field_type.__args__: # check for Optional
                    column_type = String
                    nullable = True 
            else:
                continue  # Skip fields with unhandled types

            dataclass_columns.append(Column(field.name, column_type, nullable=nullable))
    except Exception as error:
        logger.error(f"Error creating database columns {error}")

    new_table = Table(
        uuid,
        metadata,
        *dataclass_columns,
        extend_existing=True
    )
    logger.debug(f"Adding table for user {uuid}")
    try: 
        new_table.create(engine)
        logger.debug(f"Successfully added table to {database_name} {uuid}")
    except Exception as error:
        logger.error(f"Error raised while adding table {uuid} to {database_name}. Error: {error}")

def add_stock_data_to_selected_database_table(database_name: str, table_name: str, stock_data: dict):
    # Get user's stocks table reference from the database
    try:
        table_object: Table = get_table_object_from_selected_database_by_name(table_name, database_name)
        logger.debug(f"table object is {table_object}")
        if table_object is None:
            generate_table_by_id_for_selected_database(table_name, database_name)
            table_object = get_table_object_from_selected_database_by_name(table_name, database_name)
    except Exception as error:
        logger.error(f"error getting table object: {error}")

    try:
        # Create insert statement for the user stock's data
        stmt = insert(table_object).values(stock_data)
        # Get the database, execute and commit
        db: Session = next(get_db(database_name))
        # If somehow the generated uid is already in the database
        while True:
            try:
                db.execute(stmt)
                db.commit()
                break
            except Exception as error:
                logger.warning(f"Got error while inserting stock data into database. Error: {error}")
                logger.debug(f"Trying to insert with new stock record UID: {error}")
                stock_data["uid"] = generate_uuid()
        try:
            obj = db.query(table_object).order_by(table_object.c.uid.desc()).first()
        except Exception as error:
            logger.error(f"Error where finding obj: {error}")
        logger.debug(f"obj is {obj}")
        db.close()
    except Exception as error:
        logger.error(f"Could not add user's stock(s) data to database: {error}")
        db.rollback()
        logger.debug("Rolled back user's stocks database")
        return
    logger.debug(f"Done adding stock data to user {table_name}'s table")

def get_table_object_from_selected_database_by_name(table_name: str, database_name: str) -> Union[Table, None]:
    try:
        table_format, metadata, engine = get_database_variables_by_name(database_name)
        if metadata is not None:
            table_object = metadata.tables[table_name]
            return table_object
    except Exception as error:
        logger.warning(f"Could not find table {table_name} in user's stocks database: {error}")
        return None