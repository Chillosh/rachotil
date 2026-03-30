import os
import dotenv
dotenv.load_dotenv()

host = os.getenv("SSH_HOST")
user = os.getenv("SSH_USER")
password = os.getenv("SSH_PASS")