from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from records.server_response import ServerResponse
from utils.logger_script import logger
from data.database_models import Userbase
from data.database import get_db_userbase
from data.database_helper import create_user_model
from data.query_helper import user_exists
from encryption.decrypt import decrypt

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
