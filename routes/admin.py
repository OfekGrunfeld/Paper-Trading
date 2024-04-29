from fastapi import APIRouter, Request

# Modules
from utils.logger_script import logger

from records.server_response import ServerResponse
from records.database_records import DatabasesNames, UserIdentifiers

from data.userbase.helper import get_user_from_userbase, delete_user_data_from_database

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

@admin_router.get("/items")
def read_root(request: Request):
    client_host = request.client.host
    return {"client_host": client_host}