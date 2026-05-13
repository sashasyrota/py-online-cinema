import os
from email.message import EmailMessage
from unittest import mock
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from src.config.smtp.smtp_controller import sent_message
from src.database.models import Cart, OrderStatusEnum
from src.database.schemas.shopping_carts import CartDetailResponseSchema, CartListResponseSchema
from src.database.tests.conftest import get_access_token_and_user_id, create_movie, create_certification
from src.database.tests.test_movies import movie_prefix

cart_prefix = "/api/v1/shopping_carts/"

async def test_get_cart_detail_another_user_is_admin_required(
        get_access_token_and_user_id,
        create_certification,
        create_movie,
        create_user,
        create_cart,
        db,
        client
):
    access_token, user_id = await get_access_token_and_user_id()
    certification_db = await create_certification()
    movie_db = await create_movie(certification_id=certification_db.id)
    user_db = await create_user(email="TESTTEST1221@gmail.com")
    cart_db = await create_cart(movie_id=movie_db.id, user_id=user_db.id)
    await db.refresh(cart_db)
    response = await client.get(
        f"{cart_prefix}cart_detail/?cart_id={cart_db.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "You dont have permission to this action"


class TestUnauthorized:
    @pytest.mark.asyncio
    async def test_get_carts_list_is_admin_required(
            self,
            client,
    ):
        response = await client.get(f"{cart_prefix}carts/")
        assert response.status_code == 401
        assert response.json()["detail"] == 'Not authorized'

    @pytest.mark.asyncio
    async def test_get_cart_detail_is_auth_required(
            self,
            client,
    ):
        response = await client.get(f"{cart_prefix}cart_detail/")
        assert response.status_code == 401
        assert response.json()["detail"] == 'Not authorized'

    @pytest.mark.asyncio
    async def test_add_item_is_auth_required(
            self,
            client,
    ):
        response = await client.post(
            f"{cart_prefix}carts/add_item/",
            json={"movie_id": 1}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == 'Not authorized'

    @pytest.mark.asyncio
    async def test_delete_item_is_auth_required(
            self,
            client,
    ):
        response = await client.delete(
            f"{cart_prefix}carts/delete_item/1/",
        )
        assert response.status_code == 401
        assert response.json()["detail"] == 'Not authorized'


class TestAuthorized:
    @pytest.mark.asyncio
    async def test_get_carts_list_is_admin_required(
            self,
            client,
            get_access_token_and_user_id
    ):
        access_token, user_id = await get_access_token_and_user_id()
        response = await client.get(
            f"{cart_prefix}carts/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == 'You don`t have permission to this action'

    @pytest.mark.asyncio
    async def test_get_cart_detail(
            self,
            client,
            get_access_token_and_user_id,
            create_movie,
            create_certification,
            create_cart,
            db
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        cart_db = await create_cart(movie_id=movie_db.id, user_id=user_id)
        await db.refresh(cart_db)

        response = await client.get(
            f"{cart_prefix}cart_detail/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.content.decode() == CartDetailResponseSchema.model_validate(cart_db).model_dump_json()

    @pytest.mark.asyncio
    async def test_get_cart_detail_another_user_is_admin_required(
            self,
            client,
            get_access_token_and_user_id,
            create_movie,
            create_certification,
            create_cart,
            create_user,
            db
    ):
        await test_get_cart_detail_another_user_is_admin_required(
            get_access_token_and_user_id=get_access_token_and_user_id,
            client=client,
            create_user=create_user,
            create_cart=create_cart,
            create_movie=create_movie,
            create_certification=create_certification,
            db=db
        )

    @pytest.mark.asyncio
    async def test_add_item(
            self,
            client,
            get_access_token_and_user_id,
            create_movie,
            create_certification,
            create_cart,
            db
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        movie_db1 = await create_movie(certification_id=certification_db.id, name="TESTMOVIE1")
        await db.refresh(movie_db)

        no_cart_response = await client.post(
            f"{cart_prefix}carts/add_item/",
            json={"movie_id": movie_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert no_cart_response.status_code == 200

        stmt = select(Cart).filter_by(user_id=user_id)
        result = await db.execute(stmt)
        cart_db = result.unique().scalar_one_or_none()
        assert CartListResponseSchema.model_validate(cart_db).model_dump_json() == no_cart_response.content.decode()

        add_item_to_existing_cart_response = await client.post(
            f"{cart_prefix}carts/add_item/",
            json={"movie_id": movie_db1.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert add_item_to_existing_cart_response.status_code == 200
        await db.refresh(cart_db)
        assert add_item_to_existing_cart_response.content.decode() == CartListResponseSchema.model_validate(cart_db).model_dump_json()

    @pytest.mark.asyncio
    async def test_add_already_bought_movie_denied(
            self,
            client,
            get_access_token_and_user_id,
            create_movie,
            create_certification,
            create_order,
            db
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        order_db = await create_order(
            user_id=user_id,
            movie_id=movie_db.id,
            price=movie_db.price,
            status=OrderStatusEnum.PAID
        )
        await db.refresh(order_db)

        add_bought_item_to_cart_response = await client.post(
            f"{cart_prefix}carts/add_item/",
            json={"movie_id": movie_db.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert add_bought_item_to_cart_response.status_code == 400
        assert add_bought_item_to_cart_response.json()["detail"] == f"Movie with id: {movie_db.id} already purchased"

    @pytest.mark.asyncio
    async def test_delete_item(
            self,
            client,
            create_movie,
            create_certification,
            create_cart,
            get_access_token_and_user_id
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        access_token, user_id = await get_access_token_and_user_id()
        cart_db = await create_cart(movie_id=movie_db.id, user_id=user_id)
        response = await client.delete(
            f"{cart_prefix}carts/delete_item/{movie_db.id}/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 204


class TestModerator:
    @pytest.mark.asyncio
    async def test_get_cart_detail_another_user_is_admin_required(
            self,
            client,
            get_access_token_and_user_id,
            create_movie,
            create_certification,
            create_cart,
            create_user,
            db
    ):
        await test_get_cart_detail_another_user_is_admin_required(
            get_access_token_and_user_id=get_access_token_and_user_id,
            client=client,
            create_user=create_user,
            create_cart=create_cart,
            create_movie=create_movie,
            create_certification=create_certification,
            db=db
        )

    @pytest.mark.asyncio
    async def test_sent_message_func(
            self
    ):
        content = "TestContent"
        subject = "test_subject"
        recipient_email = "test_email"

        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["From"] = os.getenv("SENDER_EMAIL")
        msg["To"] = recipient_email

        with mock.patch("smtplib.SMTP") as mock_smtp:
            mock_instance = mock_smtp.return_value
            mock_instance.__enter__ = mock.Mock(return_value=mock_instance)
            mock_instance.send_message = MagicMock()
            sent_message(content=content, subject=subject, recipient_email=recipient_email)
            mock_smtp.assert_called_with("localhost", 1025)

            msg_from_mock = mock_instance.send_message.mock_calls[0].args[0]
            assert msg.items() == msg_from_mock.items()

    async def test_notify_users_in_background(
            self,
            client,
            create_movie,
            create_certification,
            create_cart,
            get_access_token_and_user_id,
            create_user,
            db
    ):
        user_db = await create_user()
        user_db.group_id = 3
        user_db.is_active = True
        certification_db = await create_certification()
        user_db1 = await create_user(email="TESTTEST1221@gmail.com")
        user_db1.group_id = 2
        user_db2 = await create_user(email="TESTTEST11221@gmail.com")
        user_db2.group_id = 2
        await db.commit()
        movie_db = await create_movie(certification_id=certification_db.id)
        cart_db = await create_cart(movie_id=movie_db.id, user_id=user_db.id)
        login_response = await client.post(f"/api/v1/accounts/login/", json={
            "email": user_db.email,
            "password": "Testtest1221!"
        })
        access_token = login_response.json()["access_token"]
        with mock.patch("src.database.routes.movies.BackgroundTasks.add_task") as mocked_obj:
            delete_response = await client.delete(
                f"{movie_prefix}movies/{movie_db.id}/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert delete_response.status_code == 204
            assert len(mocked_obj.mock_calls) == 2

