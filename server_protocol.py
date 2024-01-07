from enum import Enum
from hashlib import sha256
from sys import stdout
from validate_email import validate_email
import logger_script 

logger = logger_script.instantiate_logger()

class Constants(Enum):
    HOST_IP = "127.0.0.1"
    HOST_PORT = 5555
    SERVER_EMAIL = "ofekserver@outlook.com"
    SERVER_PASSWORD = "MyServer123"
    SMTP_SERVER_URL = "smtp-mail.outlook.com"

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