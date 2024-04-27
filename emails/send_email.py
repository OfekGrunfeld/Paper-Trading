import os
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from utils.env_variables import SERVER_EMAIL, SERVER_PASSWORD, SMTP_SERVER_URL
from utils.logger_script import logger

# class to organise different message types
class Message_Types(Enum):
  reset_password = "reset_password"
  sign_up = "sign_up"

# titles for different message types
class Message_Types_Titles(Enum):
  reset_password = "Reset Your O.G Papertrading Account's Password"
  sign_up = "Welcome to O.G Papertrading"

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
  script_dir: str = os.path.dirname(__file__)
  relative_path: str = f"{message_type}\\{message_type}"
  absolute_path: str = os.path.join(script_dir, relative_path)

  # get email message
  # in plain text
  text = None
  try:
    with open(f"{absolute_path}.txt", "r") as file:
      text = str(file.read())
  except Exception as error:
    logger.error(f"Error reading reset password text file {error}")
  # in html
  html = None
  try:
    with open(f"{absolute_path}.html", "r") as file:
      html = str(file.read())
  except Exception as error:
    logger.error(f"Error reading reset password html file {error}")
  
  # Turn the plain text/html to MIMEText objects
  part1 = MIMEText(text, "plain")
  part2 = MIMEText(html, "html")
  
  # Add HTML/plain text parts to MIMEMultipart message
  # The email client will try to render the last part first
  try:
    message.attach(part1)
    message.attach(part2)
  except Exception as error:
    logger.error(f"error: {error}")

  return message
  
def _send_email(email: str, message: MIMEMultipart) -> bool:
  """
  Sends an email to the client using the server's email

  Parameters:
    email (str): The client's email adress
    message (MIMEMultipart): The message to send to the client, (text + html)
  """
  try:
    # set message recipent
    message["To"] = email

    logger.info("Connecting to smtp server")
    # connect to smtp server
    try:
      smtp_object = smtplib.SMTP(SMTP_SERVER_URL, 587)
    except Exception as error:
      logger.error(f"Error in connecting to outlook smtp server | {error}")
      smtp_object = smtplib.SMTP_SSL(SMTP_SERVER_URL, 465)
    
    # use TTLS (for security reasons)
    try: 
      logger.info("Initialising TTLS")
      smtp_object.ehlo()
      smtp_object.starttls()
    except Exception as error:
      logger.error(f"Failed initialising TTLS while sending mail to {email}: {error}")
      smtp_object.quit()
      return False

    # log to server's email 
    try: 
      logger.info(f"logging into server's email: {SERVER_EMAIL}")
      smtp_object.login(SERVER_EMAIL, SERVER_PASSWORD) 
    except Exception as error:
      logger.error(f"Failed logging into server's email: {error}")
      smtp_object.quit()
      return False
    
    # send mail
    try:
      logger.info(f"Sending email to {email}")
      smtp_object.sendmail(SERVER_EMAIL, email, message.as_string())
      logger.info("Email sent succefully")
    except Exception as error:
      logger.error(f"Failed sending mail to {email}: {error}")
      smtp_object.quit()
      return False
    
    # close smtp session
    smtp_object.quit()
  except Exception as error:
    logger.error(f"Unknown error in sending mail to {email}")
    return False

def send_email(email: str, message_type: str) -> bool:
  try:
    message_to_send: MIMEMultipart = create_message(Message_Types_Titles[message_type], Message_Types[message_type])
    _send_email(email, message_to_send)
    return True
  except Exception as error:
    logger.error(f"Failed sending {message_type} email to {email}")
    return False