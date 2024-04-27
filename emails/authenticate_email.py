from validate_email import validate_email

from utils.env_variables import SMTP_SERVER_URL, SERVER_EMAIL
from utils.logger_script import logger

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
      dns_timeout=8, # seconds
      check_smtp=True,
      smtp_timeout=8, # seconds
      smtp_helo_host=SMTP_SERVER_URL,
      smtp_from_address=SERVER_EMAIL,
      smtp_skip_tls=False,
      smtp_tls_context=None,
      smtp_debug=False,
    )
    return is_valid
  except Exception as error:
    logger.error("Error in validating email")
    return False