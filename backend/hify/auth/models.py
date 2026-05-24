from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from hify.core.database import TimestampModel


class User(TimestampModel):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="user",
    )
