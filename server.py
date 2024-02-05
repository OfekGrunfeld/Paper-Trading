import uvicorn
from fastapi import FastAPI, Depends, HTTPException
import server_protocol as sp
from server_protocol import logger
import database_models
from database import db_base, db_engine, db_session, pending_db_base, pending_db_engine, pending_db_session
from database import verifications_db_base, verifications_db_engine, verifications_db_session
from typing import Generator
# for typehints
from sqlalchemy.orm import Session
from uuid import UUID
import send_email

# CONSTANTS
HOST_IP = sp.Constants.HOST_IP.value
HOST_PORT = sp.Constants.HOST_PORT.value

# Create FastAPI app
papertrading_app = FastAPI()

# Create database, Connect to engine
db_base.metadata.create_all(bind=db_engine)
pending_db_base.metadata.create_all(bind=pending_db_engine)
verifications_db_session.metadata.create_all(bind=verifications_db_engine)

# Get databases with generator function
def get_userbase() -> Generator[Session, any, None]:
    try:
        db = db_session()
        yield db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING USERBASE: {error}")
    finally:
        db.close()
def get_pending_userbase() -> Generator[Session, any, None]:
    try:
        pending_db = pending_db_session()
        yield pending_db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING PENDING USERBASE: {error}")
    finally:
        pending_db.close()
def get_verifications_database() -> Generator[Session, any, None]:
    try:
        verifications_db = verifications_db_session()
        yield verifications_db
    except Exception as error:
        logger.critical(f"ERROR IN GETTING VERIFICATIONS DATABASE: {error}")
    finally:
        verifications_db.close()
    
def does_username_and_password_match(user_model, username: str, password: str):
    """
    Checks if the username and password entered match the ones in the database
    
    Parameters:
        user_model (database_models.User): An existing user in the database
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
def get_user_by_username(username: str, db: Session = Depends(get_userbase)):
    try:
        # get user with id from database
        user_model = db.query(database_models.User).filter(database_models.User.username == username).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {username} does not exist"
            )
        
        return db.query(database_models.User).all()
    except Exception as error:
        logger.error(f"Failed getting user: {error}")

# FINAL (for now)
@papertrading_app.get("/database")
def get_whole_database(db: Session = Depends(get_userbase)):
    try:
        return db.query(database_models.User).all()
    except Exception as error:
        logger.error(f"Failed getting database: {error}")

# working fine
@papertrading_app.post("/sign_up")
def sign_up(email: str, username: str, password: str, 
            db: Session = Depends(get_userbase), 
            pending_db: Session = Depends(get_pending_userbase), 
            verifications_db = Depends(get_verifications_database)) -> dict[str, str | bool]:
    
    return_dict = {"sign_up_success": False, "error": ""}
    try: 
        user_model = database_models.User()

        # filter out using email or username that is already being used
        if db.query(database_models.User).filter(database_models.User.email == email).first() is not None:
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
            logger.info(f"Adding new user to the pending database: {user_model.email} | {user_model.username}")
            pending_db.add(user_model)
            pending_db.commit()
            logger.info(f"Added new user to the database: {user_model.email} | {user_model.username}")
        except Exception as error:
            logger.error(f"Failed adding user to database")
            return_dict["error"] = "Internal Server Error"
            raise HTTPException(
                status_code=500,
                detail=return_dict
            )
        
        # verify creating user - send a verification code and wait for response
        
        verification = send_email.send_email(email, send_email.Message_Types["sign_up"].value)

        return_dict["sign_up_success"] = True
        return return_dict
    except Exception as error:
        return_dict["sign_up_success"] = False
        return_dict["error"] = "Internal Server Error"
        return return_dict

def verify_sign_up(user_id: UUID, code: str) -> bool:
    
# currently deleted with username and not email / both
@papertrading_app.delete("/delete_user")
def delete_user(user_id: UUID, username: str, password: str, db: Session = Depends(get_userbase)):
    try: 
        # get user with id from database
        user_model = db.query(database_models.User).filter(database_models.User.id == user_id).first()
        
        # check if there is no such user
        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {user_id} does not exist"
            )
        
        # delete user if the username and password match the ones in the database
        if does_username_and_password_match(user_model, username, password):
            # delete user
            db.query(database_models.User).filter(database_models.User.id == user_id).delete()
            db.commit()
            return "Deleted user successfully"
        return "username or password do not match"
    except Exception as error:
        return f"Failed to delete user {error}"

# working fine
@papertrading_app.put("/update_user")
def update_user(user_id: UUID, username: str, password: str, new_username, new_password: str, db: Session = Depends(get_userbase)):
    try: 
        # don't update user if there is nothing to change
        if new_username == username and new_password == password:
            return "There is nothing to change"
        
        # get user with id from database
        user_model = db.query(database_models.User).filter(database_models.User.id == user_id).first()
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