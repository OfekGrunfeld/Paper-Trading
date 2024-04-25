import numpy as np
from typing import Union

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy import update, delete
from sqlalchemy.orm import Session

from records.server_response import ServerResponse
from utils.logger_script import logger
from data.database import get_db_userbase, DatabasesNames, get_db
from data.database_models import Userbase, UserIdentifiers
from data.database_helper import create_user_model
from data.query_helper import (user_exists, query_specific_columns_from_database_table, get_summary, 
                               get_user_from_userbase, password_matches, compile_user_portfolio,
                               delete_user_data_from_database)
from encryption.decrypt import decrypt
from encryption.userbase_encryption import encode_username, encode_password

users_router = APIRouter()

@users_router.post("/sign_up")
def sign_up(email: str, username: str, password: str, db: Session = Depends(get_db_userbase)) -> dict[str, str | bool]:
    try: 
        logger.debug(f"Received sign up request")
        return_dict = ServerResponse()
        
        email, username, password = decrypt(email), decrypt(username), decrypt(password)

        # filter out using email or username that is already being used
        if user_exists(email=email):
            return_dict.error = "Failed to sign up. Email associated with existing user"
        else:
            # save email as string, save username and password encoded sha256 to database
            # logger.info("Checking if email exists by SMTP and DNS")
            # if not is_valid_email_external(email):
            #     return_dict.error = "Invalid email address"
            if False:
                pass
            else:
                logger.info(f"Email exists: {email}")
                
                user_model = create_user_model(email, username, password)

                # add user to database
                try:
                    logger.debug(f"Adding new user to the database: {user_model.email}")
                    db.add(user_model)
                    db.commit()
                    logger.info(f"Added new user to the database: {user_model.email}")
                except Exception as error:
                    logger.error(f"Failed adding user to database. Error: {error}")
                    return_dict.reset()
                    return_dict.error = "Failed adding user to database"
                    raise HTTPException(
                        status_code=500,
                        detail=return_dict.to_dict()
                    )
                    
                # send mail to user
                # flag: bool = send_email.send_email(email, send_email.Message_Types["sign_up"])
                # if not flag:
                #     # Unsure weather to return false if email failed to send
                #     logger.warning(f"Failed sending email to user")
                return_dict.success = True
    except Exception as error:
        logger.error(f"Unexpected error occured in sign up: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict.to_dict()

@users_router.post("/sign_in")
def sign_in(username: str, password: str, db: Session = Depends(get_db_userbase)):
    try: 
        logger.debug(f"Received sign in request")
        return_dict = ServerResponse()

        username, password = decrypt(username), decrypt(password)

        # create user model with username and password
        user_model = create_user_model(None, username, password)

        # filter out using email or username that is already being used
        if not user_exists(username=username):
            logger.debug(f"Failed to sign in {username}. Non-existing user")
            return_dict.error = "Failed to sign in. Non-existing user"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        else:
            saved_user = db.query(Userbase).filter((Userbase.username == user_model.username) & (Userbase.password == user_model.password)).first()
            if saved_user is not None:
                logger.debug(f"Signed in for user {username} approved")
                return_dict.success = True
                try:
                    return_dict.data = saved_user.uuid
                except Exception as error:
                    logger.critical(f"Error while retrieving uuid from saved user: {error}")
            else:
                logger.debug(f"Signed in for user {username} has failed")
                return_dict.reset()
                return_dict.error = "Failed to sign in. Password is incorrect"
    except Exception as error:
        logger.error(f"Sign in has failed {error}")
        return_dict.error = "Sign in has failed"
        return_dict.success = False
    finally:
        logger.debug(f"sending back data: {return_dict.to_dict()}")
        return return_dict.to_dict()

@users_router.get("/get_user/database/{database_name}")
def get_user_database_table(database_name: str, uuid: str):
    try:
        return_dict = ServerResponse()
        uuid = decrypt(uuid)

        logger.debug(f"Received user portfolio request for user: {uuid}")

        results = query_specific_columns_from_database_table(database_name, uuid)
        
        return_dict.data = results
        return_dict.success = True
    except Exception as error:
        logger.error(f"Unexpected error occured in sign up: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict

@users_router.get("/get_user/summary")
def get_user_summary(uuid: str):
    try:
        return_dict = ServerResponse()
        uuid = decrypt(uuid)

        logger.debug(f"Received user portfolio request for user: {uuid}")

        results: dict = {}
        results["balance"] = np.floor(get_user_from_userbase(identifier=UserIdentifiers.uuid.value, value=uuid).balance * 100) / 100
        # Get portfolio summary
        results["symbols"] = compile_user_portfolio(DatabasesNames.portfolios.value, uuid)
        # Add current balance
        
        return_dict.data = results
        return_dict.success = True
    except Exception as error:
        logger.error(f"Unexpected error occured in sign up: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict

@users_router.put("/update/{attribute_to_update}")
def update_user(attribute_to_update: str, uuid: str, password: str, new_attribute_value: str = Query(alias="value")):
    try:
        return_dict = ServerResponse()
        uuid, password, new_attribute_value = decrypt(uuid), decrypt(password), decrypt(new_attribute_value)

        logger.debug(f"Received update request to update {attribute_to_update}")

        if password_matches(identifier=UserIdentifiers.uuid.value, identifier_value=uuid, password=password):
            try:
                session: Session = next(get_db(DatabasesNames.userbase.value))

                # Verify that attribute_to_update is a valid column name
                if hasattr(Userbase, attribute_to_update):
                    if attribute_to_update == UserIdentifiers.email.value:
                        update_values = {attribute_to_update: new_attribute_value.lower()}
                    elif attribute_to_update == UserIdentifiers.password.value:
                        update_values = {attribute_to_update: encode_password(new_attribute_value)}
                    elif attribute_to_update == UserIdentifiers.username.value:
                        update_values = {attribute_to_update: encode_username(new_attribute_value)}
                    
                    session.execute(
                        update(Userbase).
                        where(Userbase.uuid == uuid).
                        values(**update_values)  # Correct use of dictionary unpacking
                    )
                    session.commit()
                    session.close()
                    
                    return_dict.success = True
                    logger.debug(f"Changing of {attribute_to_update} has been successful")
                
            except Exception as error:
                logger.error(f"Error updating {attribute_to_update} in database. Error: {error}")
                return_dict.reset()
                return_dict.error = "Internal Server Error"
        else:
            logger.warning(f"Couldn't update {attribute_to_update} as password does not match")
    except Exception as error:
        logger.error(f"Unexpected error occured in sign up: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict

@users_router.delete("/delete/user")
def delete_user(uuid: str, password: str):
    try:
        return_dict = ServerResponse()
        # Decrypt the uuid and password
        # uuid, password = decrypt(uuid), decrypt(password)

        logger.debug(f"Received delete request for user {uuid}")

        if password_matches(identifier=UserIdentifiers.uuid.value, identifier_value=uuid, password=password):
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
        else:
            logger.warning(f"Could not delete user {uuid} as the password does not match.")
            return_dict.reset()
            return_dict.error = "Invalid password."

    except Exception as error:
        logger.error(f"Unexpected error occurred while trying to delete user {uuid}: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"

    return return_dict
