from typing import List, Dict, TypedDict

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import utils.server_protocol as sp
from utils.logger_script import logger
import data.database_models as db_m
from data.database import (db_base_userbase, db_engine_userbase,
                      db_engine_users_stocks, db_metadata_users_stocks,
                      db_engine_stocksbase, db_metadata_stocksbase)
import emails.send_email as send_email


# CONSTANTS
HOST_IP = sp.Constants.HOST_IP.value
HOST_PORT = sp.Constants.HOST_PORT.value

# Create FastAPI app
papertrading_app = FastAPI()
# Create database 
db_base_userbase.metadata.create_all(bind=db_engine_userbase)
# Create Stocksbase
db_metadata_stocksbase.create_all(bind=db_engine_stocksbase)
#create users stocks
db_metadata_users_stocks.create_all(bind=db_engine_users_stocks)

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
        return sp.encode_string(username) == user_model.username and sp.encode_string(password) == user_model.password
    except Exception as error:
        return False

@papertrading_app.get("/")
def root():
    return {"message": "Hello World"}

@papertrading_app.get("/get_user_by_username")
def get_user_by_username(username: str, db: Session = Depends(db_m.get_db_userbase)) -> List[Dict]:
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
def get_whole_database(db: Session = Depends(db_m.get_db_userbase)) -> List[Dict]:
    try:
        return db.query(db_m.Userbase).all()
    except Exception as error:
        logger.error(f"Failed getting database: {error}")

# working fine
@papertrading_app.post("/sign_up")
def sign_up(email: str, username: str, password: str, db: Session = Depends(db_m.get_db_userbase)) -> dict[str, str | bool]:
    try: 
        return_dict = sp.Response()
        user_model = db_m.Userbase()

        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.email == email).first() is not None:
            return_dict.error = "Failed to sign up. Email associated with existing user"
            return return_dict.to_dict()
        # save email as string, save username and password encoded sha256 to database
        logger.info("Checking if email exists by SMTP and DNS")
        if not sp.is_valid_email_external(email):
            return_dict.error = "Invalid email address"
            return return_dict.to_dict()
        logger.info(f"Email exists: {email}")
        
        # create user with email, username and password 
        user_model.email = email.lower()
        user_model.username = sp.encode_string(username)
        user_model.password = sp.encode_string(password)

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
        flag: bool = send_email.send_email(email, send_email.Message_Types["sign_up"].value)
        if not flag:
            # Unsure weather to return false if email failed to send
            logger.error(f"Failed sending email to user")
        return_dict.success = True
    except Exception as error:
        return_dict.success = False
        return_dict.error = "Internal Server Error"
    finally:
        return return_dict.to_dict()

# currently deleted with username and not email / both
@papertrading_app.delete("/delete_user")
def delete_user(user_id: str, username: str, password: str, db: Session = Depends(db_m.get_db_userbase)):
    try: 
        return_dict = sp.Response()
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
def force_delete_user(user_id: str, db: Session = Depends(db_m.get_db_userbase)):
    try: 
        return_dict = sp.Response()
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
def update_user(user_id: str, username: str, password: str, new_username, new_password: str, db: Session = Depends(db_m.get_db_userbase)):
    try: 
        return_dict = sp.Response()
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
            user_model.username = sp.encode_string(new_username)
        elif new_password != password:
            user_model.password = sp.encode_string(new_password)
            

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

def run_app():
    uvicorn.run(papertrading_app,host=HOST_IP, port=HOST_PORT)

if __name__ == "__main__":
    run_app()
