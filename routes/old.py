from typing import List, Dict

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from records.server_response import ServerResponse
from utils.logger_script import logger
from data.database_models import Userbase
from data.database import get_db_userbase

old_router = APIRouter()

""" EVERYTHING BELOW HERE IS NOT UPDATED FOR COMMUNICATION IN THE ENCRYPTION"""
@papertrading_app.get("/get_user_by_username")
def get_user_by_username(data: dict, db: Session = Depends(get_db_userbase)) -> List[Dict]:
    try:
        return_dict = ServerResponse()
        username = data["username"]

        # get user with uuid from database
        user_model = db.query(Userbase).filter(Userbase.username == username).first()
        
        
        # check if there is no such user
        if user_model is None:
            return_dict["error"] = f"Username: {username} does not exist"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        
        try: 
            user = db.query(Userbase).all()
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
        return_dict = ServerResponse()

        uuid, username, password, = (data["uuid"], data["username"], data["password"])
        logger.debug(f"Received request to delete user: {username}")
        # get user with uuid from database
        user_model = db.query(Userbase).filter(Userbase.uuid == uuid).first()
        
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
            db.query(Userbase).filter(Userbase.uuid == uuid).delete()
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
        return_dict = ServerResponse()
        # get user with uuid from database
        
        uuid = data["uuid"]
        user_model = db.query(Userbase).filter(Userbase.uuid == uuid).first()
        
        # check if there is no such user
        if user_model is None:
            logger.debug(f"Failed to delete user {uuid}. Non-existing user ")
            return_dict.error = "Failed to delete user. Non-existing user"
            raise HTTPException(
                status_code=404,
                detail=return_dict.to_dict()
            )
        
        # delete user
        db.query(Userbase).filter(Userbase.uuid == uuid).delete()
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
        return_dict = ServerResponse()
        # don't update user if there is nothing to change
        if new_username == username and new_password == password:
            return_dict.message = "There is nothing to change"
            return_dict.success = False
            return return_dict.to_dict()
        
        # get user with uuid from database
        user_model = db.query(Userbase).filter(Userbase.uuid == uuid).first()
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