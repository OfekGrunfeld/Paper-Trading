import uvicorn
from fastapi import FastAPI, Depends, HTTPException

from sqlalchemy.orm import Session
import server_protocol as sp
import database_models
from database import engine, Session
from pydantic import BaseModel, Field

# CONSTANTS
HOST_IP = sp.Constants.HOST_IP.value
HOST_PORT = sp.Constants.HOST_PORT.value

# create app
papertrading_app = FastAPI()
# create database, connect to engine
database_models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()

class User(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    password: str = Field(min_length=8, max_length=50)

@papertrading_app.get("/")
def root():
    return {"message": "Hello World"}

@papertrading_app.get("/database")
def Get_Database(db: Session = Depends(get_db)):
    return db.query(database_models.Userbase).all()

# working fine
@papertrading_app.post("/sign_up")
def sign_up(username: str, password: str, db: Session = Depends(get_db)):
    try: 
        user_model = database_models.Userbase()
        # save username and password encoded sha256
        user_model.username = sp.encode_string(username)
        user_model.password = sp.encode_string(password)

        # add userbase to database
        db.add(user_model)
        db.commit()

        return "signed up successfully"
    except Exception as error:
        pass

# working fine
@papertrading_app.put("/update_user/{user_id}")
def sign_up(user_id: int, username: str, password: str, new_username: str = None, new_password: str = None, db: Session = Depends(get_db)):
    try: 
        print(f"DATA: \nUser ID: {user_id}\n Username: {username}, Password: {password}\nnew_username: {new_username}, new_password: {new_password}")
        # get user with id from database
        user_model = db.query(database_models.Userbase).filter(database_models.Userbase.id == user_id).first()

        if user_model is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID: {user_id} does not exist"
            )
        encoded_username = sp.encode_string(username)
        encoded_password = sp.encode_string(password)

        if encoded_username == user_model.username and encoded_password == user_model.password:
            print("entered if")
            # for now - don't allow changing the username and password at the same time 
            if new_username is not None and new_password is not None:
                return "Cannot change both username and password"
            
            if new_username is not None:
                encoded_new_username = sp.encode_string(new_username)
                user_model.username = encoded_new_username
            if new_password is not None:
                encoded_new_password = sp.encode_string(new_password)
                user_model.password = encoded_new_password

            # add userbase to database
            db.add(user_model)
            db.commit()

            return "Update user successfully"
        return "Username and password do not match with existing user"
    except Exception as error:
        return f"Failed to update user {error}"


    

    

"""
@papertrading_app.get('/Sign_out')
def Sign_out(username: str, password: str):
    try:
        username_hash = sha256(password.encode("utf-8")).hexdigest()
        password_hash = sha256(password.encode("utf-8")).hexdigest()
        # create a query to remove usr
        query = db.Delete(users_database).where(db.and_(users_database.c.username == username_hash, users_database.c.password == password_hash))

        # get all the table data from the database
        output1 = session.execute(users_database.select()).fetchall()
        print(f"Databse:\n {output1}")

        # insert query into the database
        result = session.execute(query)

        # get all the table data from the database
        output2 = session.execute(users_database.select()).fetchall()
        print(f"Databse:\n {output2}")

        if output1 != output2:
            return "signed up succefully"
        else:
            return "Failed signing out. Wrong username or password"

    except Exception as error:
        return f"Error signing out: {error}"

@papertrading_app.get('/Authenticate')
def Authenticate(username: str, password: str):
    try:
        username_hash = sha256(password.encode("utf-8")).hexdigest()
        password_hash = sha256(password.encode("utf-8")).hexdigest()
        # create a query to find user
        query = db.select(users_database).where(db.and_(users_database.c.username == username_hash, users_database.c.password == password_hash))
        # insert query into the database
        result = session.execute(query).fetchall()

        print(result)
        if result is [] or str(result) == "[]" or result is None:
            return "Error: there is no such user"
        else:
            return f"User exists: {result}"
    except Exception as error:
        return f"Error signing out: {error}"
    return "Signed out succefully"
"""
def run_app():
    uvicorn.run(papertrading_app,host=HOST_IP, port=HOST_PORT)

if __name__ == "__main__":
    run_app()