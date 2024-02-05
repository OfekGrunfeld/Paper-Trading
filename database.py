from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_USERBASE_URL = "sqlite:///./userbase.sqlite"

# create engine for database
db_engine = create_engine(
    SQLALCHEMY_USERBASE_URL, connect_args={"check_same_thread": False}
)  

db_session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

db_base = declarative_base()



SQLALCHEMY_PENDING_USERBASE_URL = "sqlite:///./pernding_userbase.sqlite"

# create engine for database
pending_db_engine = create_engine(
    SQLALCHEMY_PENDING_USERBASE_URL, connect_args={"check_same_thread": False}
)  

pending_db_session = sessionmaker(autocommit=False, autoflush=False, bind=pending_db_engine)

pending_db_base = declarative_base()



SQLALCHEMY_VERIFICATIONS_URL = "sqlite:///./verifications.sqlite"

# create engine for database
verifications_db_engine = create_engine(
    SQLALCHEMY_VERIFICATIONS_URL, connect_args={"check_same_thread": False}
)  

verifications_db_session = sessionmaker(autocommit=False, autoflush=False, bind=verifications_db_engine)

verifications_db_base = declarative_base()
