import os
import typing
from decimal import Decimal

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from stripe import InvalidRequestError

from src.config.security.jwt_token import authorization_header, validate_access_token
from src.database.models import Cart
from src.database.models.orders import OrderStatusEnum
from src.database.models.payments import PaymentStatusEnum
from src.database.models.payments import PaymentItem
from src.database.routes.orders import get_order_item_by_order_id, get_order_by_id
from src.database.schemas.payments import PaymentCreateSchema, RefundRequestSchema
from src.database import get_async_db
from src.database.models.payments import Payment

load_dotenv()

payments = APIRouter(
    prefix="/payments"
)

client = stripe.StripeClient(os.getenv("STRIPE_SECRET_KEY"))


@payments.get("/payments/")
async def payments_list(
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header=header)
    user_id = access_token["user_id"]
    stmt = select(Payment).filter_by(user_id=user_id).order_by(Payment.created_at)
    result = await db.execute(stmt)
    payments_db = result.unique().scalars().all()
    return payments_db


@payments.post("/create_payment_request/")
async def create_payment_request(
        request: Request,
        payment_create_schema: PaymentCreateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header=header)
    order_db = await get_order_by_id(id=payment_create_schema.order_id, db=db)
    base_url = request.url_for("create_payment_complete")
    if order_db:
        if order_db.user_id == access_token["user_id"]:
            if order_db.status == OrderStatusEnum.PENDING:
                order_payment = client.v1.checkout.sessions.create({
                    "success_url": str(base_url) + "?session_id={CHECKOUT_SESSION_ID}",
                    "line_items": [
                        {
                            "price": "price_1TM3EcCurfwHcgePT29sIUUQ",
                            "quantity": int(order_db.total_amount * 100),
                        },

                    ],
                    "metadata": {"order_id": order_db.id},
                    "mode": "payment",
                })
                return {"payment_url": order_payment.url}

            elif order_db.status == OrderStatusEnum.PAID:
                raise HTTPException(status_code=400, detail=f"Order with id: {order_db.id} paid")
            raise HTTPException(status_code=400, detail=f"Order with id: {order_db.id} canceled")
        raise HTTPException(status_code=403, detail="Current user does not have this order")
    raise HTTPException(status_code=404, detail=f"Order with id: {payment_create_schema.order_id} not exist in db")


@payments.get("/create_payment_complete/")
async def create_payment_complete(
        session_id: str,
        db: AsyncSession = Depends(get_async_db),
):
    try:
        session = client.v1.checkout.sessions.retrieve(
            session_id,
        )
    except InvalidRequestError:
        raise HTTPException(status_code=404, detail="Invalid session id")


    if session["payment_status"] == "paid":
        try:
            order_db = await get_order_by_id(id=int(session["metadata"]["order_id"]), db=db)

            order_db.status = OrderStatusEnum.PAID

            payment = Payment(
                user_id=order_db.user_id,
                order_id=order_db.id,
                amount=Decimal(session["amount_total"]) / 100,
                external_payment_id=session["payment_intent"]
            )
            db.add(payment)
            await db.flush()
            for order_item in order_db.order_items:
                payment_item = PaymentItem(
                    order_item_id=order_item.id,
                    payment_id=payment.id,
                    price_at_payment=order_item.price_at_order
                )
                db.add(payment_item)
                await db.flush()
            stmt_cart = select(Cart).filter_by(user_id=order_db.user_id)
            result = await db.execute(stmt_cart)
            cart_db = result.unique().scalar_one_or_none()
            await db.delete(cart_db)

            await db.commit()
            return {"Payment complete successful": True}

        except IntegrityError as exc:
            await db.rollback()
            client.v1.refunds.create({"payment_intent": session["payment_intent"]})
            raise exc
    raise HTTPException(status_code=400, detail="Transaction failed")


@payments.post("/refund_payment/")
async def create_refund_payment(
        refund_schema: RefundRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header=header)
    user_id = access_token["user_id"]

    stmt = select(Payment).filter(
        Payment.user_id == user_id,
        Payment.order_id == refund_schema.order_id,
        Payment.status == PaymentStatusEnum.SUCCESSFUL
    )
    result = await db.execute(stmt)
    payment_db = result.unique().scalar_one_or_none()
    order_db = await get_order_by_id(id=refund_schema.order_id, db=db)
    if not payment_db:
        raise HTTPException(status_code=404, detail="Payment not found")

    try:
        client.v1.refunds.create({"payment_intent": payment_db.external_payment_id})
        payment_db.status = PaymentStatusEnum.REFUNDED
        order_db.status = OrderStatusEnum.CANCELED
        await db.commit()
        return {"Payment was returned": True}
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    except InvalidRequestError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
