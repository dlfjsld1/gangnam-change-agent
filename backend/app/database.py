import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db_models import Base

DEFAULT_DATABASE_URL = "sqlite:///./storage/gangnam-change-agent.db"


def configured_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or configured_database_url()
    parsed_url = make_url(url)
    connect_args: dict[str, object] = {}
    engine_options: dict[str, object] = {}
    if parsed_url.get_backend_name() == "sqlite":
        connect_args["check_same_thread"] = False
        _prepare_sqlite_directory(parsed_url.database)
        if parsed_url.database == ":memory:":
            engine_options["poolclass"] = StaticPool
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        **engine_options,
    )


class Database:
    def __init__(self, database_url: str | None = None) -> None:
        self.engine = create_database_engine(database_url)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise


def _prepare_sqlite_directory(database_path: str | None) -> None:
    if not database_path or database_path == ":memory:":
        return
    Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
