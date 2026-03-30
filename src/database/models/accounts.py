import datetime
import enum
from typing import Optional

from sqlalchemy import String, func, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database.models.base import Base


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class GenderEnum(str, enum.Enum):
    MAN = "man"
    WOMAN = "woman"
    
    
class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum]
    users = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now())
    group_id: Mapped[id] = mapped_column(Integer, ForeignKey("user_groups.id"))
    group = relationship("UserGroup", back_populates="users")
    profile = relationship("Profile", uselist=False, back_populates="user")


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
    user = relationship("User", back_populates="profile")