from typing import List, Dict
import datetime
import traceback

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import yfinance as yf
import numpy as np

from utils import encode_string, decrypt
from emails.authenticate_email import is_valid_email_external
from utils.response import Response
from utils.logger_script import logger
from utils.constants import HOST_IP, HOST_PORT 
import data.database_models as db_m
from data.database import (db_base_userbase, db_engine_userbase,
                      db_engine_transactions, db_metadata_transactions,
                      get_db_userbase, get_db_transactions)
from data import StockRecord
import emails.send_email as send_email

# Create FastAPI app
papertrading_app = FastAPI()
# Create database 
db_base_userbase.metadata.create_all(bind=db_engine_userbase)
#create users stocks
db_metadata_transactions.create_all(bind=db_engine_transactions)


def does_username_and_password_match(user_model, username: str, password: str):
    """
    Checks if the username and password entered match the ones in the database
    
    Parameters:
        :param user_model: An existing user in the database
        :param username: username
        :param password: password
    
    Returns:
        True: if the encoded username matches the user's username in the database and the encoded password matches the user's password in the database
    """
    try:
        return encode_string(username) == user_model.username and encode_string(password) == user_model.password
    except Exception as error:
        return False

@papertrading_app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        request.state.data = decrypt(request.state.data)
    except Exception as error:
        # logger.warning(f"Either there is no data in request state or decryption has failed. Error: {error}")
        pass
    response = await call_next(request)
    return response

@papertrading_app.get("/")
def root():
    return {"message": "Hello World"}


@papertrading_app.post("/sign_up")
def sign_up(email: str, username: str, password: str, db: Session = Depends(get_db_userbase)) -> dict[str, str | bool]:
    try: 
        logger.debug(f"Received sign up request")
        return_dict = Response()
        user_model = db_m.Userbase()

        email, username, password = decrypt(email), decrypt(username), decrypt(password)
        logger.debug(f"Email: {email}, username: {username}, password: {password}")
        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.email == email).first() is not None:
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
                
                # create user with email, username and password 
                user_model.email = email.lower()
                user_model.username = encode_string(username)
                user_model.password = encode_string(password)

                # add user to database
                try:
                    logger.info(f"Adding new user to the database: {user_model.email}")
                    db.add(user_model)
                    db.commit()
                    logger.info(f"Added new user to the database: {user_model.email}")
                except Exception as error:
                    logger.error(f"Failed adding user to database: {error}")
                    return_dict.reset()
                    return_dict.error = "Failed adding user to database"
                    raise HTTPException(
                        status_code=500,
                        detail=return_dict.to_dict()
                    )
                    
                # send mail to user
                flag: bool = send_email.send_email(email, send_email.Message_Types["sign_up"])
                if not flag:
                    # Unsure weather to return false if email failed to send
                    logger.warning(f"Failed sending email to user")
                return_dict.success = True
    except Exception as error:
        logger.error(f"Unexpected error occured in sign up: {error}")
        return_dict.reset()
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict.to_dict()

@papertrading_app.post("/sign_in")
def sign_in(username: str, password: str, db: Session = Depends(get_db_userbase)):
    try: 
        logger.debug(f"Received sign in request")
        return_dict = Response()
        user_model = db_m.Userbase()

        username, password = decrypt(username), decrypt(password)

        # create user model with username and password
        user_model.username = encode_string(username)
        user_model.password = encode_string(password)

        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.username == user_model.username).first() is None:
            logger.debug(f"Failed to sign in {username}. Non-existing usern ")
            return_dict.error = "Failed to sign in. Non-existing user"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        else:
            saved_user = db.query(db_m.Userbase).filter((db_m.Userbase.username == user_model.username) & (db_m.Userbase.password == user_model.password)).first()
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


@papertrading_app.post("/submit_order")
def submit_order(uuid: str, order: str, db: Session = Depends(get_db_userbase)):
    try:
        uuid, order = decrypt(uuid), decrypt(order)
        return_dict = Response()

        try:
            logger.debug(f"Got order: {order} from user {uuid}")
        except Exception as error:
            logger.error(f"Format of order is wrong: {order}. Error: {error}")

        try:
            info = yf.Ticker(order["symbol"]).info
        except Exception as error:
            logger.error(f"Failed to get info of stock from yfinance: {error}")


        match(order["order_type"]):
            case "market":
                return_dict.success = True
                total_cost = total_cost=np.float64(np.float64(order["shares"]) * np.float64(info["currentPrice"]))
                sr = StockRecord(
                    timestamp=datetime.datetime.now(),
                    symbol=order["symbol"],
                    side=order["side"],
                    order_type=order["order_type"],
                    shares=order["shares"],
                    total_cost=total_cost,
                    status="",  
                    notes=None
                )
                # for debugging currently
                db_m.add_stock_to_transaction_history_table(uuid, sr.to_dict())

                saved_user = db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).first()
                
                bal = saved_user.balance
                saved_user.balance = bal - total_cost
                db.commit()
                logger.debug(f"Updated {uuid}'s balance to: {saved_user.balance}")
            
            case _:
                return_dict.error = f"Invalid or unsupported order type"
            
        
        return return_dict
    except Exception as error:
        logger.error(f"Error submitting order {error}")
        return None

""" EVERYTHING BELOW HERE IS NOT UPDATED FOR COMMUNICATION IN THE ENCRYPTION"""
@papertrading_app.get("/get_user_by_username")
def get_user_by_username(data: dict, db: Session = Depends(get_db_userbase)) -> List[Dict]:
    try:
        return_dict = Response()
        username = data["username"]

        # get user with uuid from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.username == username).first()
        
        
        # check if there is no such user
        if user_model is None:
            return_dict["error"] = f"Username: {username} does not exist"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        
        try: 
            user = db.query(db_m.Userbase).all()
            return_dict.data = str(user)
        except Exception as error:
            logger.error(f"Failed querying user in database: {error}")
            return_dict.reset()
            return_dict.error = f"Failed querying user in database"
            raise HTTPException(
                status_code=500,
                detail=return_dict.to_dict()
            )
    except Exception as error:
        logger.error(f"Failed getting user: {error}")
        return_dict.reset()
        return_dict.error = f"Failed getting user"
        raise HTTPException(
            status_code=500,
            detail=return_dict.to_dict()
        )
    finally:
        return return_dict.to_dict()

# currently deleted with username and not email / both
@papertrading_app.delete("/delete_user")
def delete_user(data: dict, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()

        uuid, username, password, = (data["uuid"], data["username"], data["password"])
        logger.debug(f"Received request to delete user: {username}")
        # get user with uuid from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).first()
        
        # check if there is no such user
        if user_model is None:
            logger.debug(f"Failed to delete user {username}. Non-existing user ")
            return_dict.error = "Failed to delete user. Non-existing user"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        
        # delete user if the username and password match the ones in the database
        if does_username_and_password_match(user_model, username, password):
            # delete user
            db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).delete()
            db.commit()
            return_dict.data = "Deleted user successfully"
            return_dict.success = True
        else:
            return_dict.error = "Could not deleted user as the username and password do not match"
            return_dict.success = False
    except Exception as error:
        logger.error(f"Failed to delete user {username}. Error: {error}")
        return_dict.reset()
        return_dict.error = f"Failed to delete user. Internal server error"
        return_dict.success = False
    finally:
        return return_dict.to_dict()

@papertrading_app.delete("/force_delete_user")
def force_delete_user(data: dict, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()
        # get user with uuid from database
        
        uuid = data["uuid"]
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).first()
        
        # check if there is no such user
        if user_model is None:
            logger.debug(f"Failed to delete user {uuid}. Non-existing user ")
            return_dict.error = "Failed to delete user. Non-existing user"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        
        # delete user
        db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).delete()
        db.commit()
        # update return dict
        return_dict.data = "Deleted user successfully"
        return_dict.success = True
    except Exception as error:
        logger.error(f"Failed to delete user {uuid}. Error: {error}")
        return_dict.reset()
        return_dict.error = f"Failed to delete user. Internal server error"
        return_dict.success = False
    finally:
        return return_dict.to_dict()

# unupdated because function should be later removed
@papertrading_app.put("/update_user")
def update_user(uuid: str, username: str, password: str, new_username, new_password: str, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()
        # don't update user if there is nothing to change
        if new_username == username and new_password == password:
            return_dict.message = "There is nothing to change"
            return_dict.success = False
            return return_dict.to_dict()
        
        # get user with uuid from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.uuid == uuid).first()
        # raise exception if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {uuid} does not exist"
            )
        # if username and password do not match user don't continue
        if not does_username_and_password_match(user_model, username, password):
            return_dict.message = "Username and password do not match with existing user"
            return_dict.success = False
            return return_dict.to_dict()
        
        # don't allow to change both username and password at the same time
        # used return because if / elif would change the first 
        if new_username != username and new_password != password:
            return_dict.message = "Cannot update both username and password at the same time"
            return_dict.success = False
            return return_dict.to_dict()
        
        # change username or password to new username or new password
        if new_username != username:
            user_model.username = encode_string(new_username)
        elif new_password != password:
            user_model.password = encode_string(new_password)
            

        # add User to database
        db.add(user_model)
        db.commit()

        return_dict.message = f"Updated user {username} successfully"
        return_dict.success = True
    except Exception as error:
        return_dict.message = ""
        return_dict.error = f"Failed to update user {error}"
        return_dict.success = False
    finally:
        return return_dict.to_dict()

def run_app() -> None:
    uvicorn.run(
        papertrading_app,
        host=HOST_IP,
        port=int(HOST_PORT),
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem",
    )

if __name__ == "__main__":
    run_app()
