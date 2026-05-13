import datetime
import decimal
import enum
import typing

from sqlalchemy import ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base

if typing.TYPE_CHECKING:
    from src.database.models.movies import Movie


class OrderStatusEnum(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        default=OrderStatusEnum.PENDING
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=decimal.Decimal("0.00")
    )
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="joined"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False
    )
    order: Mapped[Order] = relationship(back_populates="order_items")
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"), nullable=False
    )
    movie: Mapped["Movie"] = relationship(back_populates="order_items")
    price_at_order: Mapped[decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )
