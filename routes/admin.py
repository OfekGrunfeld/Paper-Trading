import numpy as np
import traceback

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy import update
from sqlalchemy.orm import Session
import yfinance as yf

# Modules
from utils.logger_script import logger
from utils.stock_handler import StockHandler
from utils.encryption import decrypt

from records.stock_record import StockRecord
from records.server_response import ServerResponse
from records.database_records import DatabasesNames, UserIdentifiers

from data.get_databases import get_db, get_db_userbase
from data.userbase.model import Userbase
from data.userbase.helper import (get_user_from_userbase, create_user_model, password_matches, delete_user_data_from_database, 
                                  get_user_from_userbase, check_uniqueness_of_email_and_or_username)
from data.userbase.encryption import encode_username, encode_password
from data.dynamic_databases.helper import query_specific_columns_from_database_table, compile_user_portfolio

admin_router = APIRouter()

@admin_router.delete("/force_delete_user")
def force_delete_user(uuid: str):
    try:
        return_dict = ServerResponse()
    
        user = get_user_from_userbase(identifier=UserIdentifiers.uuid.value, value=uuid)
        
        # Attempt to delete user data from userbase, transactions, and portfolios databases
        success_userbase = delete_user_data_from_database(uuid, DatabasesNames.userbase.value)
        success_transactions = delete_user_data_from_database(uuid, DatabasesNames.transactions.value)
        success_portfolios = delete_user_data_from_database(uuid, DatabasesNames.portfolios.value)

        if success_userbase and success_transactions and success_portfolios:
            logger.info(f"User {uuid} and all associated data have been successfully deleted.")
            return_dict.success = True
        else:
            logger.error(f"Failed to fully delete user {uuid} and associated data.")
            return_dict.reset()
            return_dict.error = "Partial or no data was deleted."
    except Exception as error:
        logger.warning(f"Error: {error}")
    finally:
        return return_dict.to_dict()

