import os


os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app import models  # noqa: E402, F401
from app.database import Base, engine  # noqa: E402


Base.metadata.create_all(engine)
