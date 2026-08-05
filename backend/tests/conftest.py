import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app import models  # noqa: F401
from app.database import Database

Database().create_schema()
