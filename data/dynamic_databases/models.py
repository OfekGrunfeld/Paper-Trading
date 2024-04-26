from typing import Union, get_type_hints, Literal
from dataclasses import fields
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import Column, String, Table, DateTime, Double, Engine, MetaData
import numpy as np

from data.database import DatabasesNames
from data.get_databases import get_database_variables_by_name
from data.utils.uuid import generate_uuid

from utils.logger_script import logger
from records.stock_record import StockRecord

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