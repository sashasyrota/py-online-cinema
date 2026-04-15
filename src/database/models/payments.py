import datetime
import decimal
import enum
import typing

from sqlalchemy import ForeignKey, DateTime, func, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base

if typing.TYPE_CHECKING:
    from database.models.accounts import User


class PaymentStatusEnum(enum.Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="payments")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[PaymentStatusEnum] = mapped_column(default=PaymentStatusEnum.SUCCESSFUL)
    amount: Mapped[decimal] = mapped_column(DECIMAL(10,2), nullable=False)
    external_payment_id: Mapped[str] = mapped_column(nullable=True)


class PaymentItem(Base):
    __tablename__ = "payment_items"
    __table_args__ = {"extend_existing": True}


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), nullable=False)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    price_at_payment: Mapped[decimal] = mapped_column(DECIMAL(10,2), nullable=False)
