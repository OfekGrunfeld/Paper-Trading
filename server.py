from typing import List, Dict
import datetime
import traceback

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import yfinance as yf
import numpy as np

from utils import encode_string
from emails.authenticate_email import is_valid_email_external
from utils.response import Response
from utils.logger_script import logger
from utils.constants import HOST_IP, HOST_PORT 
import data.database_models as db_m
from data.database import (db_base_userbase, db_engine_userbase,
                      db_engine_transaction_history, db_metadata_transaction_history,
                      get_db_userbase, get_db_transaction_history)
from data import StockRecord
import emails.send_email as send_email

# Create FastAPI app
papertrading_app = FastAPI()
# Create database 
db_base_userbase.metadata.create_all(bind=db_engine_userbase)
#create users stocks
db_metadata_transaction_history.create_all(bind=db_engine_transaction_history)


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

@papertrading_app.get("/")
def root():
    return {"message": "Hello World"}

@papertrading_app.get("/get_user_by_username")
def get_user_by_username(username: str, db: Session = Depends(get_db_userbase)) -> List[Dict]:
    try:
        # get user with id from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.username == username).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {username} does not exist"
            )
        
        try: 
            user = db.query(db_m.Userbase).all()
            return user
        except Exception as error:
            logger.error(f"Failed querying user in database: {error}")
            return None
    except Exception as error:
        logger.error(f"Failed getting user: {error}")

# FINAL (for now)
@papertrading_app.get("/database")
def get_whole_database(db: Session = Depends(get_db_userbase)) -> List[Dict]:
    try:
        return db.query(db_m.Userbase).all()
    except Exception as error:
        logger.error(f"Failed getting database: {error}")

# working fine
@papertrading_app.post("/sign_up")
def sign_up(email: str, username: str, password: str, db: Session = Depends(get_db_userbase)) -> dict[str, str | bool]:
    try: 
        logger.debug(f"Received sign up request")
        return_dict = Response()
        user_model = db_m.Userbase()

        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.email == email).first() is not None:
            return_dict.error = "Failed to sign up. Email associated with existing user"
            return return_dict.to_dict()
        # save email as string, save username and password encoded sha256 to database
        logger.info("Checking if email exists by SMTP and DNS")
        if not is_valid_email_external(email):
            return_dict.error = "Invalid email address"
            return return_dict.to_dict()
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
            logger.error(f"Failed adding user to database")
            return_dict.error = "Internal Server Error"
            raise HTTPException(
                status_code=500,
                detail=return_dict
            )
            
        # send mail to user
        flag: bool = send_email.send_email(email, send_email.Message_Types["sign_up"])
        if not flag:
            # Unsure weather to return false if email failed to send
            logger.error(f"Failed sending email to user")
        return_dict.success = True
    except Exception as error:
        return_dict.success = False
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict.to_dict()

@papertrading_app.post("/sign_in")
def sign_in(username: str, password: str, db: Session = Depends(get_db_userbase)):
    try: 
        logger.debug(f"Received sign in request")
        return_dict = Response()
        user_model = db_m.Userbase()

        # create user model with username and password
        user_model.username = encode_string(username)
        user_model.password = encode_string(password)

        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.username == user_model.username).first() is None:
            logger.debug(f"Signed in for user {username} has failed")
            return_dict.error = "Failed to sign in. Non-existing user"
            raise HTTPException(
                    status_code=404,
                    detail=return_dict.to_dict()
                )
        else:
            saved_user = db.query(db_m.Userbase).filter((db_m.Userbase.username == user_model.username) & (db_m.Userbase.password == user_model.password)).first()
            if saved_user:
                logger.debug(f"Signed in for user {username} approved")
                return_dict.success = True
                try:
                    return_dict.extra = saved_user.id
                except Exception as error:
                    logger.critical(f"Expected error where yes {error}")
            else:
                logger.debug(f"Signed in for user {username} has failed")
                return_dict.error = "Failed to sign in. Password is incorrect"
    except Exception as error:
        return_dict.message = f"Sign in has failed{error}"
        return_dict.success = False
    finally:
        return return_dict.to_dict()

# currently deleted with username and not email / both
@papertrading_app.delete("/delete_user")
def delete_user(user_id: str, username: str, password: str, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()
        # get user with id from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.id == user_id).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {user_id} does not exist"
            )
        
        # delete user if the username and password match the ones in the database
        if does_username_and_password_match(user_model, username, password):
            # delete user
            db.query(db_m.Userbase).filter(db_m.Userbase.id == user_id).delete()
            db.commit()
            return_dict.message = "Deleted user successfully"
            return_dict.success = True
        else:
            return_dict.message = "Deleted user successfully"
            return_dict.success = False
    except Exception as error:
        return_dict.message = f"Failed to delete user {error}"
        return_dict.success = False
    finally:
        return return_dict.to_dict()

@papertrading_app.delete("/force_delete_user")
def force_delete_user(user_id: str, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()
        # get user with id from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.id == user_id).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {user_id} does not exist"
            )
        
        # delete user
        db.query(db_m.Userbase).filter(db_m.Userbase.id == user_id).delete()
        db.commit()
        # update return dict
        return_dict.message = "Deleted user successfully"
        return_dict.success = True
    except Exception as error:
        return_dict.message = ""
        return_dict.error = f"Failed to delete user {error}"
        return_dict.success = False
    finally:
        return return_dict.to_dict()
# working fine
@papertrading_app.put("/update_user")
def update_user(user_id: str, username: str, password: str, new_username, new_password: str, db: Session = Depends(get_db_userbase)):
    try: 
        return_dict = Response()
        # don't update user if there is nothing to change
        if new_username == username and new_password == password:
            return_dict.message = "There is nothing to change"
            return_dict.success = False
            return return_dict.to_dict()
        
        # get user with id from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.id == user_id).first()
        # raise exception if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {user_id} does not exist"
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

@papertrading_app.post("/submit_order")
def submit_order(data: dict, db: Session = Depends(get_db_userbase)):
    try:
        return_dict = Response()
        
        try:
            logger.debug(f"Got order: {data["order"]} from user {data["id"]}")
        except Exception as error:
            logger.error(f"Format of order is wrong: {data}. Error: {error}")

        
        try:
            info = yf.Ticker(data["order"]["symbol"]).info
        except Exception as error:
            logger.error(f"Failed to get info of stock from yfinance: {error}")


        match(data["order"]["order_type"]):
            case "market":
                return_dict.success = True
                total_cost = total_cost=np.float64(np.float64(data["order"]["shares"]) * np.float64(info["currentPrice"]))
                sr = StockRecord(
                    timestamp=datetime.datetime.now(),
                    symbol=data["order"]["symbol"],
                    side=data["order"]["side"],
                    order_type=data["order"]["order_type"],
                    shares=data["order"]["shares"],
                    total_cost=total_cost,
                    notes=None
                )
                db_m.add_stock_to_transaction_history_table(data["id"], sr.to_dict())

                saved_user = db.query(db_m.Userbase).filter(db_m.Userbase.id == data["id"]).first()
                
                bal = saved_user.balance
                logger.critical(f"Balance: {bal}")
                saved_user.balance = bal - total_cost
                db.commit()
                logger.critical(f"new balance: {saved_user.balance}")
            
            case _:
                return_dict.error = f"Invalid or unsupported order type"
                return return_dict
            
        
            

        return return_dict
    except Exception as error:
        logger.error(f"Error submitting order {error}")
        traceback.print_exc()
        return None
                

def run_app() -> None:
    uvicorn.run(papertrading_app,host=HOST_IP, port=HOST_PORT)

if __name__ == "__main__":
    run_app()
