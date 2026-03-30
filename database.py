import os
from sqlalchemy import create_engine

DB_URI = os.environ.get("DB_URI")
engine = create_engine(DB_URI, pool_pre_ping=True)

db_config = {
    'host': os.environ.get("DB_HOST"),
    'user': os.environ.get("DB_USER"),
    'password': os.environ.get("DB_PASSWORD"),
    'database': os.environ.get("DB_NAME")
}
