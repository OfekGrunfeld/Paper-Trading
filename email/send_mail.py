import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from enum import Enum
import validate_email

SERVER_EMAIL = "ofekserver@outlook.com"
SERVER_PASSWORD = "MyServer123"
SMTP_SERVER_URL = "smtp-mail.outlook.com"

# class to organise different message types
class Message_Types(Enum):
  reset_password = "reset_password"

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
      dns_timeout=10, # seconds
      check_smtp=True,
      smtp_timeout=10, # seconds
      smtp_helo_host=SMTP_SERVER_URL,
      smtp_from_address=SERVER_EMAIL,
      smtp_skip_tls=False,
      smtp_tls_context=None,
      smtp_debug=False,
    )
    return is_valid
  except Exception as error:
    print("Error in validating email")
    return False

def create_message(message_title: str, message_type: str) -> MIMEMultipart:
  """
  Creates an email message with the given message type

  Parameters:
    message_title (str): Title of email
    message_type (str): Type of message to create; e.g reset_password, delete_account, etc.

    Returns:
    A MIMEMultipart message made with both plain text and html
  """

  # initialize message
  message = MIMEMultipart("alternative")
  message["Subject"] = message_title
  message["From"] = SERVER_EMAIL
  
  # get absoulte path of email message
  script_dir = os.path.dirname(__file__)
  relative_path = f"{message_type}/{message_type}"
  absolute_path = os.path.join(script_dir, relative_path)

  # get email message
  # in plain text
  text = None
  try:
    with open(f"{absolute_path}.txt", "r") as file:
        text = str(file.read())
  except Exception as error:
    print(f"Error reading reset password text file {error}")
  # in html
  html = None
  try:
    with open(f"{absolute_path}.html", "r") as file:
      html = str(file.read())
  except Exception as error:
    print(f"Error reading reset password html file {error}")
  print(f"text: {text}\nhtml: {html}")
  
  # Turn the plain text/html to MIMEText objects
  part1 = MIMEText(text, "plain")
  part2 = MIMEText(html, "html")
  
  # Add HTML/plain text parts to MIMEMultipart message
  # The email client will try to render the last part first
  message.attach(part1)
  message.attach(part2)

  return message
  
def send_mail(client_email: str, message: MIMEMultipart) -> None:
  """
  Sends an email to the client using the server's email

  Parameters:
    client_email (str): The client's email adress
    message (MIMEMultipart): The message to send to the client, (text + html)
  """
  # set message recipent
  message["To"] = client_email

  print("Connecting to smtp server")
  # connect to smtp server
  try:
    smtp_object = smtplib.SMTP(SMTP_SERVER_URL, 587)
  except Exception as error:
    print(f"Error in connecting to outlook smtp server | {error}")
    smtp_object = smtplib.SMTP_SSL(SMTP_SERVER_URL, 465)
  
  print("Initialising TTLS")
  # user TTLS (for security reasons)
  smtp_object.ehlo()
  smtp_object.starttls()

  print(f"Logging in to server's email: {SERVER_EMAIL}")
  # log to server email
  smtp_object.login(SERVER_EMAIL, SERVER_PASSWORD) 
  # send mail
  print(f"Sending email to {client_email}")
  smtp_object.sendmail(SERVER_EMAIL, client_email, message.as_string())
  print("Email sent succefully")

  # close smtp session
  smtp_object.quit()

def main():
  send_mail("yarimi347@gmail.com", create_message("Ata Nagar", Message_Types.reset_password.value))

if __name__ == "__main__":
  main()
