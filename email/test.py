from validate_email import validate_email

SERVER_EMAIL = "ofekserver@outlook.com"
SERVER_PASSWORD = "MyServer123"
SMTP_SERVER_URL = "smtp-mail.outlook.com"

def is_valid_email(client_email: str):
  """
  Checks if a given email is valid
  
  Parameters:
    client_email (str): Email adress to check

  Returns:
    Is valid email, in terms of:
    1. Format 
    2. Not in blacklist 
    3. Can create route to email adress with DNS (Valid MX Record) 
    4. Initiation of SMTP with email adress worked
  """
  try:
    is_valid = validate_email(
      email_address=client_email,
      check_format=True,
      check_blacklist=True,
      check_dns=True,
      dns_timeout=5, # seconds
      check_smtp=True,
      smtp_timeout=5, # seconds
      smtp_helo_host=SMTP_SERVER_URL,
      smtp_from_address=SERVER_EMAIL,
      smtp_skip_tls=False,
      smtp_tls_context=None,
      smtp_debug=False,
    )
    return is_valid
  except Exception as error:
    print(f"Error in validating email\n{error}")
    return False
  
if __name__ == "__main__":
  print(is_valid_email("tamargri24@gmail.com"))
