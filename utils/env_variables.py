from os import getenv
from dotenv import load_dotenv

HOST_IP = getenv("HOST_IP")
HOST_PORT = getenv("HOST_PORT")

SERVER_EMAIL = getenv("SERVER_EMAIL")
SERVER_PASSWORD = getenv("SERVER_PASSWORD")
SMTP_SERVER_URL = getenv("SMTP_SERVER_URL")

START_BALANCE = getenv("START_BALANCE")

SECRET_KEY = getenv("SECRET_KEY")

if __name__ == "__main__":
    load_dotenv()