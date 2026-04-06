import datetime
import enum
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, func, DateTime, Integer, ForeignKey, Text, Date
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.config.security.password import hash_password, verify_password
from src.database.models.base import Base

# if TYPE_CHECKING:
#     from src.database.models.profiles import UserProfile


class GenderEnum(str, enum.Enum):
    MAN = "man"
    WOMAN = "woman"


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"



class UserGroup(Base):
    __tablename__ = "user_groups"
    __table_args__ = {'extend_existing': True}


    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[UserGroupEnum]
    users: Mapped[List["User"]] = relationship(back_populates="group")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    group_id: Mapped[id] = mapped_column(Integer, ForeignKey("user_groups.id"))
    group: Mapped[UserGroup] = relationship(back_populates="users")
    user_profile: Mapped["UserProfile"] = relationship(uselist=False, back_populates="user", lazy="joined")
    activation_tokens: Mapped[List["ActivationToken"]] = relationship(back_populates="user", cascade="all, delete")
    password_reset_token: Mapped["PasswordResetToken"] = relationship(back_populates="user", lazy="joined")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user")

    @property
    def password(self):
        return self.hashed_password

    @password.setter
    def password(self, value):
        self.hashed_password = hash_password(value)

    def check_password(self, value):
        return verify_password(
            plain_password=value,
            hashed_password=self.hashed_password
        )


class Token:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActivationToken(Token, Base):
    __tablename__ = "activation_tokens"
    __table_args__ = {'extend_existing': True}

    user: Mapped["User"] = relationship(back_populates="activation_tokens", lazy="joined")


class PasswordResetToken(Token, Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {'extend_existing': True}

    user: Mapped["User"] = relationship(back_populates="password_reset_token", lazy="joined")


class RefreshToken(Token, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'extend_existing': True}

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class UserProfile(Base):
    __tablename__ = "profiles"
    __table_args__ = {'extend_existing': True}


    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))
    avatar: Mapped[str] = mapped_column(nullable=False)
    gender: Mapped[GenderEnum]
    date_of_birth: Mapped[Optional[datetime.date]] = mapped_column(Date)
    info: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    user: Mapped["User"] =  relationship(back_populates="user_profile", lazy="joined")
