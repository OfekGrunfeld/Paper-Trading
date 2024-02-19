import uvicorn
from fastapi import FastAPI, Depends, HTTPException

import utils.server_protocol as sp
from utils.server_protocol import logger
import data.database_models as db_m
from data.database import (db_base_userbase, db_engine_userbase,
                      db_engine_users_stocks, db_metadata_users_stocks,
                      db_engine_stocksbase, db_metadata_stocksbase)

import emails.send_email as send_email
# for typehints
from sqlalchemy.orm import Session
from uuid import UUID

# CONSTANTS
HOST_IP = sp.Constants.HOST_IP.value
HOST_PORT = sp.Constants.HOST_PORT.value

# Create FastAPI app
papertrading_app = FastAPI()
# Create database 
db_base_userbase.metadata.create_all(bind=db_engine_userbase)
# Create Stocksbase
db_metadata_stocksbase.create_all(db_engine_stocksbase)
#create users stocks
db_metadata_users_stocks.create_all(db_engine_users_stocks)

def does_username_and_password_match(user_model, username: str, password: str):
    """
    Checks if the username and password entered match the ones in the database
    
    Parameters:
        user_model (db_m.Userbase): An existing user in the database
        username (str): username
        password (str): password
    
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
def get_user_by_username(username: str, db: Session = Depends(sp.get_db_userbase)):
    try:
        # get user with id from database
        user_model = db.query(db_m.Userbase).filter(db_m.Userbase.username == username).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {username} does not exist"
            )
        
        return db.query(db_m.Userbase).all()
    except Exception as error:
        logger.error(f"Failed getting user: {error}")

# FINAL (for now)
@papertrading_app.get("/database")
def get_whole_database(db: Session = Depends(sp.get_db_userbase)):
    try:
        return db.query(db_m.Userbase).all()
    except Exception as error:
        logger.error(f"Failed getting database: {error}")

# working fine
@papertrading_app.post("/sign_up")
def sign_up(email: str, username: str, password: str, db: Session = Depends(sp.get_db_userbase)) -> dict[str, str | bool]:
    return_dict = {"sign_up_success": False, "error": ""}
    try: 
        user_model = db_m.Userbase()

        # filter out using email or username that is already being used
        if db.query(db_m.Userbase).filter(db_m.Userbase.email == email).first() is not None:
            return_dict["error"] = "Failed to sign up. Email associated with existing user"
            return return_dict
        # save email as string, save username and password encoded sha256 to database
        logger.info("Checking if email exists by SMTP and DNS")
        if not sp.is_valid_email_external(email):
            return_dict["error"] = "Invalid email address"
            return return_dict
        logger.info(f"Email exists: {email}")
        
        # create user with email, username and password 
        user_model.email = email.lower()
        user_model.username = sp.encode_string(username)
        user_model.password = sp.encode_string(password)

        # add user to database
        try:
            logger.info(f"Adding new user to the database: {user_model}")
            db.add(user_model)
            db.commit()
            logger.info(f"Added new user to the database: {user_model}")
        except Exception as error:
            logger.error(f"Failed adding user to database")
            return_dict["error"] = "Internal Server Error"
            raise HTTPException(
                status_code=500,
                detail=return_dict
            )
            

        # send mail to user
        flag = send_email.send_email(email, send_email.Message_Types["sign_up"].value)
        if not return_dict:
            # Unsure weather to return false if email failed to send
            logger.error(f"Failed sending email to user")
        return_dict["sign_up_success"] = True
        return return_dict
    except Exception as error:
        return_dict["sign_up_success"] = False
        return_dict["error"] = "Internal Server Error"

# currently deleted with username and not email / both
@papertrading_app.delete("/delete_user")
def delete_user(user_id: UUID, username: str, password: str, db: Session = Depends(sp.get_db_userbase)):
    try: 
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
            return "Deleted user successfully"
        return "username or password do not match"
    except Exception as error:
        return f"Failed to delete user {error}"

# working fine
@papertrading_app.put("/update_user")
def update_user(user_id: UUID, username: str, password: str, new_username, new_password: str, db: Session = Depends(sp.get_db_userbase)):
    try: 
        # don't update user if there is nothing to change
        if new_username == username and new_password == password:
            return "There is nothing to change"
        
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
            return "Username and password do not match with existing user"
        
        # don't allow to change both username and password at the same time
        # used return because if / elif would change the first 
        if new_username != username and new_password != password:
            return "Cannot update both username and password at the same time"
        
        # change username or password to new username or new password
        if new_username != username:
            user_model.username = sp.encode_string(new_username)
        elif new_password != password:
            user_model.password = sp.encode_string(new_password)
            

        # add User to database
        db.add(user_model)
        db.commit()

        return f"Updated user {username} successfully"
    except Exception as error:
        return f"Failed to update user {error}"

def run_app():
    uvicorn.run(papertrading_app,host=HOST_IP, port=HOST_PORT)

if __name__ == "__main__":
    run_app()