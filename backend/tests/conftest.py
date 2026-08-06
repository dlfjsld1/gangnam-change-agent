import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app import models  # noqa: F401
from app.main import database

database.create_schema()
