import datetime
from typing import List

from sqlalchemy import ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from src.database.models.base import Base


if TYPE_CHECKING:
    from src.database.models.movies import Movie


class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)
    cart: Mapped["Cart"] = relationship(back_populates="cart_items")
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped["Movie"] = relationship(back_populates="cart_items")
    added_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="cart_movie_uc"),
    )

class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    cart_items: Mapped[List[CartItem]] = relationship(back_populates="cart", lazy="joined")