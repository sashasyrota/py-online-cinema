import os
from unittest.mock import patch

import pytest
import stripe
from sqlalchemy import select

from src.database.models import (
    OrderStatusEnum,
    Payment,
    PaymentStatusEnum,
    CartItem,
)

payment_prefix = "/api/v1/payments/"


class TestUnauthorized:
    @pytest.mark.asyncio
    async def test_create_payment_request_is_auth_required(
        self,
        client,
    ):
        response = await client.post(
            f"{payment_prefix}create_payment_request/", json={"order_id": 1}
        )
        assert response.json()["detail"] == "Not authorized"
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_payment_complete_is_auth_required(
        self,
        client,
    ):
        response = await client.get(
            f"{payment_prefix}create_payment_complete/?session_id=12231sf"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Invalid session id"

    @pytest.mark.asyncio
    async def test_payment_list_is_auth_required(
        self,
        client,
    ):
        response = await client.get(f"{payment_prefix}payments/")
        assert response.json()["detail"] == "Not authorized"
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_refund_payment_is_auth_required(
        self,
        client,
    ):
        response = await client.post(
            f"{payment_prefix}refund_payment/", json={"order_id": 1}
        )
        assert response.json()["detail"] == "Not authorized"
        assert response.status_code == 401


class TestAuthorized:
    @pytest.mark.asyncio
    async def test_create_payment(
        self,
        client,
        create_certification,
        create_movie,
        get_access_token_and_user_id,
        create_cart,
        create_order,
        db,
    ):
        stripe_client = stripe.StripeClient(os.getenv("_KEY", "sk_test_51TLo3FCurfwHcgePDJqMxlltkjVh7Y9fu6FJK4R6j9qixxnZbLqz4TJJa6nFKW95wzVHWzRm7y3coaD7bK0LEI4W00alAMwRhV"))
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        await create_cart(movie_id=movie_db.id, user_id=user_id)
        order_db = await create_order(
            user_id=user_id,
            movie_id=movie_db.id,
            price=movie_db.price,
        )
        request_response = await client.post(
            f"{payment_prefix}create_payment_request/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert "payment_url" in request_response.json().keys()
        assert request_response.status_code == 200
        session_query = request_response.json()["payment_url"].split("/")[-1]
        session_id = session_query.split("#")[0]

        stripe_session = stripe_client.v1.checkout.sessions.retrieve(
            session_id
        )
        price = int(float(movie_db.price) * 100)
        assert stripe_session["currency"] == "usd"
        assert int(stripe_session["amount_total"]) == price

        with patch(
            "src.database.routes.payments.client.v1.checkout.sessions.retrieve"
        ) as mocked_stripe:
            mocked_stripe.return_value = {
                "payment_status": "paid",
                "metadata": {"order_id": order_db.id},
                "amount_total": price,
                "payment_intent": "0183",
            }

            complete_response = await client.get(
                f"{payment_prefix}create_payment_complete/",
                params={"session_id": session_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert complete_response.status_code == 200
            assert complete_response.json() == {
                "Payment complete successful": True
            }
            await db.refresh(order_db)
            assert order_db.status == OrderStatusEnum.PAID
            stmt = select(Payment).filter_by(order_id=order_db.id)
            result = await db.execute(stmt)
            payment_db = result.unique().scalar_one_or_none()
            assert payment_db.status == PaymentStatusEnum.SUCCESSFUL
            stmt = select(CartItem).filter_by(movie_id=movie_db.id)
            result = await db.execute(stmt)
            cart_item_db = result.unique().scalar_one_or_none()
            assert cart_item_db is None

    async def test_create_canceled_payment_denied(
        self, client, get_access_token_and_user_id
    ):
        access_token, user_id = await get_access_token_and_user_id()
        with patch(
            "src.database.routes.payments.client.v1.checkout.sessions.retrieve"
        ) as mocked_stripe:
            mocked_stripe.return_value = {
                "payment_status": "unpaid",
            }

            response = await client.get(
                f"{payment_prefix}create_payment_complete/",
                params={"session_id": "test_session_id"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.json()["detail"] == "Transaction failed"
            assert response.status_code == 400

    async def test_create_payment_with_purchased_and_canceled_order_denied(
        self,
        client,
        create_certification,
        create_movie,
        get_access_token_and_user_id,
        create_cart,
        create_order,
        db,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        await create_cart(movie_id=movie_db.id, user_id=user_id)
        order_db = await create_order(
            user_id=user_id,
            movie_id=movie_db.id,
            price=movie_db.price,
        )
        order_db.status = OrderStatusEnum.PAID
        await db.commit()
        request_response = await client.post(
            f"{payment_prefix}create_payment_request/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert request_response.status_code == 400
        assert (
            request_response.json()["detail"]
            == f"Order with id: {order_db.id} paid"
        )

        order_db.status = OrderStatusEnum.CANCELED
        await db.commit()
        request_response = await client.post(
            f"{payment_prefix}create_payment_request/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert request_response.status_code == 400
        assert (
            request_response.json()["detail"]
            == f"Order with id: {order_db.id} canceled"
        )

    async def test_create_payment_with_incorrect_order_id_denied(
        self,
        client,
        get_access_token_and_user_id,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        request_response = await client.post(
            f"{payment_prefix}create_payment_request/",
            json={"order_id": 1},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert (
            request_response.json()["detail"]
            == "Order with id: 1 not in db"
        )
        assert request_response.status_code == 404

    async def test_create_payment_with_order_another_user_denied(
        self,
        client,
        create_certification,
        create_movie,
        get_access_token_and_user_id,
        create_user,
        create_cart,
        create_order,
        db,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        user1 = await create_user(email="TESTTEST1@gmail.com")
        await create_cart(movie_id=movie_db.id, user_id=user1.id)
        order_db = await create_order(
            user_id=user1.id,
            movie_id=movie_db.id,
            price=movie_db.price,
        )
        request_response = await client.post(
            f"{payment_prefix}create_payment_request/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert (
            request_response.json()["detail"]
            == "Current user does not have this order"
        )
        assert request_response.status_code == 403

    async def test_refund_payment(
        self,
        client,
        create_certification,
        create_movie,
        get_access_token_and_user_id,
        create_user,
        create_cart,
        create_order,
        db,
        create_payment,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        await create_cart(movie_id=movie_db.id, user_id=user_id)
        order_db = await create_order(
            user_id=user_id,
            movie_id=movie_db.id,
            price=movie_db.price,
        )
        payment_not_found_response = await client.post(
            f"{payment_prefix}refund_payment/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert (
            payment_not_found_response.json()["detail"] == "Payment not found"
        )
        assert payment_not_found_response.status_code == 404
        payment_db = await create_payment(
            user_id=user_id, order_id=order_db.id, amount=movie_db.price
        )

        with patch(
            "src.database.routes.payments.client.v1.refunds.create"
        ) as mocked_stripe:
            successful_refund_response = await client.post(
                f"{payment_prefix}refund_payment/",
                json={"order_id": order_db.id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert successful_refund_response.json() == {
                "Payment was returned": True
            }
            assert mocked_stripe.mock_calls[0].args[0] == {
                "payment_intent": str(payment_db.external_payment_id)
            }

            duplicate_refund_response = await client.post(
                f"{payment_prefix}refund_payment/",
                json={"order_id": order_db.id},
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert (
                duplicate_refund_response.json()["detail"]
                == "Payment not found"
            )
            assert duplicate_refund_response.status_code == 404

    async def test_refund_payment_another_user_denied(
        self,
        client,
        create_certification,
        create_movie,
        create_user,
        create_cart,
        create_order,
        db,
        create_payment,
        get_access_token_and_user_id,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        user_db = await create_user(email="TESTTEST@gmail.com")
        await create_cart(movie_id=movie_db.id, user_id=user_db.id)
        order_db = await create_order(
            user_id=user_db.id,
            movie_id=movie_db.id,
            price=movie_db.price,
        )
        await create_payment(
            user_id=user_db.id, order_id=order_db.id, amount=movie_db.price
        )
        refund_response_denied = await client.post(
            f"{payment_prefix}refund_payment/",
            json={"order_id": order_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert refund_response_denied.json()["detail"] == "Payment not found"
        assert refund_response_denied.status_code == 404
