import json

import pytest
from httpx import AsyncClient
from httpx._types import RequestFiles
from sqlalchemy import select

from src.database.models import User, RefreshToken, UserProfile

account_prefix = "/api/v1/accounts/"


async def get_token_model_by_token(token_model, token, db):
    stmt_refresh_tokens = select(token_model).filter_by(token=token)
    result = await db.execute(stmt_refresh_tokens)
    refresh_token_db = result.unique().scalar_one_or_none()
    return refresh_token_db


async def get_account_response(
    client: AsyncClient,
    route_url: str,
    body_params: dict = None,
    headers: dict = None,
    data: dict = None,
    files: RequestFiles = None,
):
    response = await client.post(
        f"{account_prefix}{route_url}",
        json=body_params,
        headers=headers,
        data=data,
        files=files,
    )
    return response


class TestUnauthorized:
    @pytest.mark.asyncio
    async def test_account_register_fields(self, client: AsyncClient, db):
        email = "testtest1112111@gmail.com"
        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "Qwerty1221!"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 201
        assert "email" in decode_response
        assert "activation_token" in decode_response

        stmt = select(User)
        result = await db.execute(stmt)
        new_test_user = result.unique().scalar_one_or_none()
        assert new_test_user.email == email

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "Qwerty1221"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should consist one of these symbols {'/.!&?,'}"
        )

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "Qwertysasd/"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should consist at least one digit"
        )

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "Qwerty"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should be not shorter than 8 characters"
        )

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "123124124324/"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should consist at least one upper-case letter"
        )

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "qeqwetqyu4/"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should consist at least one upper-case letter"
        )

        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": "TESTTEST1/"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 400
        assert (
            decode_response["detail"]
            == "Password should consist at least one lower-case letter"
        )

    @pytest.mark.asyncio
    async def test_account_activate(self, client, db):
        email = "testtest11111211@gmail.com"
        password = "Qwerty1221!"
        response = await get_account_response(
            client=client,
            route_url="register/",
            body_params={"email": email, "password": password},
        )
        json_content = json.loads(response.content.decode())

        activate_response = await get_account_response(
            client=client, route_url="activate/", body_params=json_content
        )
        assert activate_response.status_code == 200

        activate_forbidden_response = await get_account_response(
            client=client,
            route_url="activate/",
            body_params={"email": email, "activation_token": "invalid_token"},
        )
        assert activate_forbidden_response.status_code == 400

        stmt = select(User)
        result = await db.execute(stmt)
        test_user = result.unique().scalar_one_or_none()
        assert test_user.is_active is True

    @pytest.mark.asyncio
    async def test_account_login(self, client, db, create_user):
        db_user = await create_user()
        response = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response = json.loads(response.content.decode())
        assert decode_response["detail"] == "User account is not active"
        assert response.status_code == 403

        db_user.is_active = True
        await db.commit()
        response = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert "access_token" in decode_response
        assert "refresh_token" in decode_response

        refresh_token_db = await get_token_model_by_token(
            RefreshToken, decode_response["refresh_token"], db
        )
        assert refresh_token_db is not None

    @pytest.mark.asyncio
    async def test_account_reset_request_and_complete(
        self, client, db, create_user
    ):
        db_user = await create_user()
        response = await client.post(
            "api/v1/accounts/reset-request/", json={"email": db_user.email}
        )
        decode_response = json.loads(response.content.decode())
        assert decode_response["detail"] == "User account is not active"
        assert response.status_code == 403

        db_user.is_active = True
        await db.commit()
        response = await get_account_response(
            client=client,
            route_url="reset-request/",
            body_params={"email": db_user.email},
        )
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert "reset_token" in decode_response

        response_valid_token = await get_account_response(
            client=client,
            route_url="reset-complete/",
            body_params={
                "reset_token": decode_response["reset_token"],
                "password": "NewPassword1221!",
            },
        )
        decode_response = json.loads(response_valid_token.content.decode())
        assert response.status_code == 200
        assert decode_response == {"User password reset complete": True}

        response_invalid_token = await get_account_response(
            client=client,
            route_url="reset-complete/",
            body_params={
                "reset_token": "invalid_token",
                "password": "NewPassword1221!",
            },
        )
        decode_response = json.loads(response_invalid_token.content.decode())
        assert response_invalid_token.status_code == 400
        assert decode_response["detail"] == "Not enough segments"

        response_invalid_token = await get_account_response(
            client=client,
            route_url="reset-complete/",
            body_params={
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                               ".eyJ1c2VyX2lkIjoxfQ"
                               ".SHRALNlfZeIZv30Zxkhmf74jOwgo8XAkD5MPky6eT0Y",
                "password": "NewPassword1221!",
            },
        )
        decode_response = json.loads(response_invalid_token.content.decode())
        assert response_invalid_token.status_code == 400
        assert decode_response["detail"] == "Signature verification failed."

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, db, create_user):
        db_user = await create_user()
        db_user.is_active = True
        await db.commit()

        response_login = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response_login = json.loads(response_login.content.decode())

        response_refresh_token = await get_account_response(
            client=client,
            route_url="refresh/",
            body_params={
                "refresh_token": decode_response_login["refresh_token"]
            },
        )
        decode_response_refresh_token = json.loads(
            response_refresh_token.content.decode()
        )

        assert response_refresh_token.status_code == 200
        assert "access_token" in decode_response_refresh_token

    @pytest.mark.asyncio
    async def test_account_logout(self, client, db, create_user):
        db_user = await create_user()
        db_user.is_active = True
        await db.commit()

        response_login = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response_login = json.loads(response_login.content.decode())

        response_logout = await get_account_response(
            client=client,
            route_url="logout/",
            body_params={
                "refresh_token": decode_response_login["refresh_token"]
            },
            headers={
                "Authorization":
                    f"Bearer {decode_response_login["access_token"]}"
            },
        )
        assert response_logout.status_code == 200

        refresh_token_db = await get_token_model_by_token(
            RefreshToken, decode_response_login["refresh_token"], db
        )
        assert refresh_token_db is None


class TestAuthorized:
    @pytest.mark.asyncio
    async def test_create_user_profile(
        self, client, create_user, db, image_in_memory
    ):
        db_user = await create_user()
        db_user.is_active = True
        await db.commit()
        response_login = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response_login = json.loads(response_login.content.decode())

        response_create_profile_without_avatar = await get_account_response(
            client=client,
            route_url="create_profile/",
            data={
                "first_name": "Testfirstname",
                "last_name": "Testlastname",
                "gender": "man",
                "date_of_birth": "2000-01-12",
                "info": "Testinfo",
            },
        )
        decode_response_create_profile_without_avatar = json.loads(
            response_create_profile_without_avatar.content.decode()
        )
        assert decode_response_create_profile_without_avatar["detail"] == [
            {
                "type": "missing",
                "loc": ["body", "avatar"],
                "msg": "Field required",
                "input": None,
            }
        ]
        assert response_create_profile_without_avatar.status_code == 422
        response_create_profile_without_info = await get_account_response(
            client=client,
            route_url="create_profile/",
            data={
                "first_name": "Testfirstname",
                "last_name": "Testlastname",
                "gender": "man",
                "date_of_birth": "2000-01-12",
            },
            files={"avatar": image_in_memory},
        )
        decode_response_create_profile_without_info = json.loads(
            response_create_profile_without_info.content.decode()
        )
        assert decode_response_create_profile_without_info["detail"] == [
            {
                "type": "missing",
                "loc": ["body", "info"],
                "msg": "Field required",
                "input": None,
            }
        ]
        assert response_create_profile_without_info.status_code == 422

        test_profile_data = {
            "first_name": "Testfirstname",
            "last_name": "Testlastname",
            "gender": "man",
            "date_of_birth": "2000-01-12",
            "info": "Testinfo",
        }

        response_successful_create_profile = await get_account_response(
            client=client,
            route_url="create_profile/",
            headers={
                "Authorization":
                    f"Bearer {decode_response_login["access_token"]}"
            },
            data=test_profile_data,
            files={"avatar": image_in_memory},
        )
        stmt_user_profile = select(UserProfile).filter(
            UserProfile.user_id == db_user.id
        )
        result = await db.execute(stmt_user_profile)
        profile_db = result.unique().scalar_one_or_none()
        assert response_successful_create_profile.status_code == 200
        assert profile_db is not None

        decode_response_successful_create_profile = json.loads(
            response_successful_create_profile.content.decode()
        )
        test_profile_data |= {"avatar": f"avatar_{profile_db.user_id}.jpeg"}
        for field, value in test_profile_data.items():
            assert value == decode_response_successful_create_profile[field]

    @pytest.mark.asyncio
    async def test_change_account_state_is_admin_required(
        self, client, create_user, db
    ):
        db_user = await create_user()
        db_user.is_active = True
        await db.commit()

        response_login = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response_login = json.loads(response_login.content.decode())

        user_change_state_response = await get_account_response(
            route_url="change_account/",
            client=client,
            body_params={
                "user_id": db_user.id,
                "group_id": 3,
                "is_active": True,
            },
            headers={
                "Authorization":
                    f"Bearer {decode_response_login["access_token"]}"
            },
        )
        decode_user_change_state_response = json.loads(
            user_change_state_response.content.decode()
        )

        assert user_change_state_response.status_code == 403
        assert (
            decode_user_change_state_response["detail"]
            == "Not enough permissions for this operation"
        )


class TestIsAdmin:
    @pytest.mark.asyncio
    async def test_change_account_state_is_admin_required(
        self, client, create_user, db
    ):
        db_user = await create_user()
        db_user.is_active = True
        db_user.group_id = 3
        await db.commit()

        db_user1 = User(email="test1test1@test.com", group_id=1)
        db_user1.password = "Testpassword12!"
        db.add(db_user1)
        await db.commit()

        response_login = await get_account_response(
            client=client,
            route_url="login/",
            body_params={"email": db_user.email, "password": "Testtest1221!"},
        )
        decode_response_login = json.loads(response_login.content.decode())

        user_change_state_response = await get_account_response(
            route_url="change_account/",
            client=client,
            body_params={
                "user_id": db_user1.id,
                "group_id": 3,
                "is_active": True,
            },
            headers={
                "Authorization":
                    f"Bearer {decode_response_login["access_token"]}"
            },
        )
        await db.refresh(db_user1)
        assert user_change_state_response.status_code == 200
        assert db_user1.is_active is True
        assert db_user1.group_id == 3
