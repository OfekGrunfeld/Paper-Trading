from sqlalchemy import Column, String, Double
import numpy as np

from data.database import DatabasesNames
from data.database import db_base_userbase
from data.utils.uuid import generate_uuid

from utils.env_variables import START_BALANCE

class Userbase(db_base_userbase):
    """
    Userbase databse:
    uuid: uuid | EMAIL: string | USERNAME: string | PASSWORD: string
    """
    __tablename__ = "userbase"

    uuid = Column(String, primary_key=True, default=generate_uuid, unique=True)
    
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    balance = Column(Double, nullable=False, default=np.double(START_BALANCE)) 

    def __str__(self) -> str:
        try:
            return f"uuid: {self.uuid}, email: {self.email}, username: {self.username}, password: {self.password}, balance: {self.balance}"
        except Exception as error:
            return f"Failed creating string: {error}"