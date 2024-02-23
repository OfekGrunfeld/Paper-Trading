from enum import Enum
from hashlib import sha256
from sys import stdout
from os import getenv


from validate_email import validate_email
from dotenv import load_dotenv

from utils.logger_script import logger
from data.database import get_db_userbase, get_db_users_stock

def get_db_userbase():
   return get_db_userbase()

def get_db_users_stock():
   return get_db_users_stock()
   
class Constants(Enum):
    load_dotenv()
    HOST_IP = "127.0.0.1"
    HOST_PORT = 5555

    SERVER_EMAIL = getenv("SERVER_EMAIL")
    SERVER_PASSWORD = getenv("SERVER_PASSWORD")
    SMTP_SERVER_URL = getenv("SMTP_SERVER_URL")

    # root_path = os.path.dirname(os.path.realpath(__file__))

def encode_string(string: str) -> str:
    """
    Encode a given string using the SHA-256 hashing algorithm.

    Parameters:
        string (str): The input string to be encoded.

    Returns:
        str: A hexadecimal representation of the SHA-256 hash of the input string.
    """
    if string is None:
        return False
    return sha256(string.encode("utf-8")).hexdigest()

def is_valid_email_external(email_adress: str):
  """
  Checks if a given email is valid
  
  Parameters:
    email_adress (str): Email adress to check

  Returns:
    Is valid email, in terms of:
    1. Format 
    2. Not in blacklist 
    3. Can create route to email adress with DNS (Valid MX Record) 
    4. Initiation of SMTP with email adress worked
  """
  try:
    is_valid = validate_email(
      email_address=email_adress,
      check_format=True,
      check_blacklist=True,
      check_dns=True,
      dns_timeout=10, # seconds
      check_smtp=True,
      smtp_timeout=10, # seconds
      smtp_helo_host=Constants.SMTP_SERVER_URL.value,
      smtp_from_address=Constants.SERVER_EMAIL.value,
      smtp_skip_tls=False,
      smtp_tls_context=None,
      smtp_debug=False,
    )
    return is_valid
  except Exception as error:
    print("Error in validating email")
    return False