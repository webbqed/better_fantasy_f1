import os

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url is None:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

# pool_pre_ping checks each pooled connection is still alive before use and
# transparently reconnects if not. Hosted Postgres often drops idle connections,
# which otherwise surfaces as an intermittent 500 on the first request after idle.
engine = create_engine(database_url, pool_pre_ping=True)