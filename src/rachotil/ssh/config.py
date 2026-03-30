import os
from dotenv import load_dotenv
load_dotenv()

HOST = os.getenv("SSH_HOST")
USER = os.getenv("SSH_USER")
PASSWORD = os.getenv("SSH_PASSWORD")