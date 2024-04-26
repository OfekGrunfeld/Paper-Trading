from typing import Optional, Union, Optional
from data.userbase.model import Userbase

from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from data.get_databases import get_database_variables_by_name
from data.userbase.encryption import encode_username, encode_password
from data.get_databases import get_db

from utils.logger_script import logger
from records.database_records import UserIdentifiers
from records.database_records import DatabasesNames

def create_user_model(email: Optional[str], username: str, password: str) -> Union[Userbase, None]:
    """
    Creates a new user model by optionally assigning a provided email, and always assigning an encoded username and encoded password.
    Email is optional but username and password are mandatory for user creation.

    Args:
        email (Optional[str]): The email address of the user. It is converted to lowercase before being stored. Can be None.
        username (str): The username of the user. It is encoded using SHA-256 hashing before being stored.
        password (str): The password of the user. It is encoded using MD5 hashing before being stored.

    Returns:
        Userbase or None: Returns a `Userbase` instance initialized with the provided credentials if the required inputs (username and password) are valid.
                          Returns `None` if the required inputs are not provided, indicating incomplete user data.
    """
    if username is None or password is None:
        logger.error("Cannot create a user without a username or password.")
        return None

    user_model = Userbase()

    # Normalize and encode the user credentials
    if email and email != "" or email != None:
        user_model.email = email.lower()  # Normalize email to lowercase

    user_model.username = encode_username(username)
    user_model.password = encode_password(password) 

    return user_model

def get_user_from_userbase(identifier: str, value: str) -> Union[Userbase, None]:
    """
    Fetches a user from the database based on the provided identifier and value,
    excluding the possibility to search by password for security reasons.

    Args:
        identifier (str): The identifier type, which can be 'uuid', 'email', or 'username'.
        value (str): The value corresponding to the identifier.

    Returns:
        Userbase: The Userbase object if found, None otherwise.
    """
    # Disallow searching by password
    if identifier == UserIdentifiers.password.value:
        logger.error("Searching by password is not allowed.")
        return None
    if identifier not in UserIdentifiers:
        logger.error(f"Identifier is not one of the supported identifiers. Chosen identifier: {identifier}.")
        return None

    try:
        db_userbase: Session = next(get_db(DatabasesNames.userbase.value))
        # Dynamically set the attribute to filter on based on the identifier
        filter_condition = getattr(Userbase, identifier) == value
        user_model = db_userbase.query(Userbase).filter(filter_condition).one()
        return user_model
    except NoResultFound:
        logger.info(f"No user found with {identifier} = {value}.")
        return None
    except Exception as error:
        logger.error(f"Error retrieving user from database: {error}")
        return None
    finally:
        db_userbase.close()

from typing import Tuple, Optional
import logging

def check_uniqueness_of_email_and_or_username(email: Optional[str] = None, username: Optional[str] = None) -> Tuple[bool, Optional[Union[Tuple[str], Tuple[str,str]]]]:
    """
    Check the uniqueness of email and/or username in the database.

    Parameters:
        email (Optional[str]): The email to check for uniqueness.
        username (Optional[str]): The username to check for uniqueness.

    Returns:
        Tuple[bool, Optional[str]]: A tuple containing a boolean indicating if the email and/or username is unique,
                                    and a string indicating what is not unique ("email", "username", "both", or None if both are unique).
    """
    if email is None and username is None:
        logging.warning("Both fields to check uniqueness (email and username) are empty. Please enter one.")
        return False, None

    session: Session = next(get_db(DatabasesNames.userbase.value))  # Assume get_db is correctly imported and configured
    try:
        not_unique = []
        if email:
            email_exists = session.query(Userbase).filter(Userbase.email == email).first()
            if email_exists:
                not_unique.append("email")

        if username:
            username_exists = session.query(Userbase).filter(Userbase.username == encode_username(username)).first()
            if username_exists:
                not_unique.append("username")

        if not_unique:
            return (False, tuple(not_unique))
        return True, None
    except Exception as error:
        logging.error(f"Error occurred while checking uniqueness. Error: {error}")
        return False, None
    finally:
        session.close()
    
def password_matches(identifier: str, identifier_value: str, password: str) -> bool:
    saved_user = get_user_from_userbase(identifier, identifier_value)

    if saved_user is None:
        return False
    else:
        return saved_user.password == encode_password(password)

def delete_user_data_from_database(uuid: str, database_name: str) -> bool:
    """
    Deletes user data from a specified database. If the database is 'userbase', it deletes only the specific user's row.
    Otherwise, it attempts to delete a table named after the user's UUID (used for transaction and portfolio databases).

    Args:
        uuid (str): The user's UUID.
        database_name (str): The name of the database from which to delete the user's data.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    try:
        if database_name == DatabasesNames.userbase.value:
            session = next(get_db(database_name))
            # Execute the delete operation for a specific user in the userbase
            user = session.query(Userbase).filter(Userbase.uuid == uuid).delete()
            session.commit()
            logger.info(f"Successfully deleted user data for UUID {uuid} from userbase.")
            return True
        else:
            # Retrieve database configurations
            _, metadata, engine = get_database_variables_by_name(database_name)
            if metadata is None or engine is None:
                logger.warning(f"Database setup not found for {database_name}")
                return False

            session = Session(bind=engine)
            # Get the table from metadata which is named after the user's UUID
            user_table = metadata.tables.get(uuid)
            if user_table is not None:
                # Execute the delete operation for the entire table
                session.execute(delete(user_table))
                session.commit()
                logger.info(f"Successfully deleted all data for user {uuid} from {database_name}.")
                return True
            else:
                logger.warning(f"No table found for user {uuid} in database {database_name}.")
                return False
    except Exception as error:
        logger.error(f"Failed to delete data for user {uuid} from {database_name}: {error}")
        return False
    finally:
        session.close()
        logger.warning(f"Even here")
    