import os

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url is None:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

engine = create_engine(database_url)