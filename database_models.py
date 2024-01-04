import sqlalchemy as db
from database import Base

class Users(Base):
    __tablename__ = 'userbase'
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)