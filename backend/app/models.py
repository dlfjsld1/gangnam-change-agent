from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppState(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, object] | list[dict[str, object]]] = mapped_column(JSON)
