import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from enum import Enum
from server_protocol import is_valid_email_external, Constants

# class to organise different message types
class Message_Types(Enum):
  reset_password = "reset_password"

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
  message["From"] = Constants.SERVER_EMAIL.value
  
  # get absoulte path of email message
  script_dir = os.path.dirname(__file__)
  relative_path = f"emails\{message_type}\{message_type}"
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
  try:
    message.attach(part1)
    message.attach(part2)
  except Exception as error:
    print(f"error: {error}")

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
    smtp_object = smtplib.SMTP(Constants.SMTP_SERVER_URL.value, 587)
  except Exception as error:
    print(f"Error in connecting to outlook smtp server | {error}")
    smtp_object = smtplib.SMTP_SSL(Constants.SMTP_SERVER_URL.value, 465)
  
  print("Initialising TTLS")
  # user TTLS (for security reasons)
  smtp_object.ehlo()
  smtp_object.starttls()

  print(f"Logging in to server's email: {Constants.SERVER_EMAIL.value}")
  # log to server email
  smtp_object.login(Constants.SERVER_EMAIL.value, Constants.SERVER_PASSWORD.value) 
  # send mail
  print(f"Sending email to {client_email}")
  smtp_object.sendmail(Constants.SERVER_EMAIL.value, client_email, message.as_string())
  print("Email sent succefully")

  # close smtp session
  smtp_object.quit()

def main():
  email_to_send_to = "shahar.arpaly@gmail.com"
  if is_valid_email_external(email_to_send_to):
    send_mail(email_to_send_to, create_message("Ata Nagar", Message_Types.reset_password.value))
  else:
    pass

if __name__ == "__main__":
  main()
