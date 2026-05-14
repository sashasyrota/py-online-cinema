import pytest
from sqlalchemy import select

from src.database.models import Order, OrderStatusEnum
from src.database.schemas.orders import OrderResponseDetailSchema

order_prefix = "/api/v1/orders/"


class TestUnauthorized:
    @pytest.mark.asyncio
    async def test_create_order_is_auth_required(self, client):
        response = await client.post(f"{order_prefix}create_order/")
        assert response.json()["detail"] == "Not authorized"
        assert response.status_code == 401


class TestAuthorized:
    @pytest.mark.asyncio
    async def test_create_order(
        self,
        client,
        get_access_token_and_user_id,
        create_movie,
        create_cart,
        create_certification,
        db,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        await create_cart(movie_id=movie_db.id, user_id=user_id)
        response = await client.post(
            f"{order_prefix}create_order/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 201
        stmt = select(Order).filter_by(user_id=user_id)
        result = await db.execute(stmt)
        order_db = result.unique().scalar_one_or_none()
        assert (
            response.content.decode()
            == OrderResponseDetailSchema.model_validate(
                order_db
            ).model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_cancel_order(
        self,
        client,
        get_access_token_and_user_id,
        create_movie,
        create_cart,
        create_certification,
        db,
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        await create_cart(movie_id=movie_db.id, user_id=user_id)
        await client.post(
            f"{order_prefix}create_order/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        stmt = select(Order).filter_by(user_id=user_id)
        result = await db.execute(stmt)
        order_db = result.unique().scalar_one_or_none()
        cancel_pending_order_response = await client.post(
            f"{order_prefix}cancel_order/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"order_id": order_db.id},
        )
        await db.refresh(order_db)
        assert (
            cancel_pending_order_response.content.decode()
            == OrderResponseDetailSchema.model_validate(
                order_db
            ).model_dump_json()
        )

        order_db.status = OrderStatusEnum.PAID
        await db.commit()
        cancel_paid_order_denied_response = await client.post(
            f"{order_prefix}cancel_order/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"order_id": order_db.id},
        )
        assert cancel_paid_order_denied_response.status_code == 400
        assert (
            cancel_paid_order_denied_response.json()["detail"]
            == "You can cancel only pending order."
        )
