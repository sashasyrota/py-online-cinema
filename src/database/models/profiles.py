import datetime
import enum
from typing import Optional

from sqlalchemy import Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base
from database.models.accounts import User


class GenderEnum(str, enum.Enum):
    MAN = "man"
    WOMAN = "woman"


class UserProfile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))
    avatar: Mapped[str] = mapped_column(nullable=False)
    gender: Mapped[GenderEnum]
    date_of_birth: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    info: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    user: Mapped["User"] =  relationship("User", back_populates="profile")
