import json
import os
import sqlite3

import pytest
from fastapi.params import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_db
from database.models import User, RefreshToken
from database.routes.accounts import accounts, refresh_token
from main import app

account_prefix = "/api/v1/accounts/"


async def get_token_model_by_token(token_model, token, db):
    stmt_refresh_tokens = select(token_model).filter_by(token=token)
    result = await db.execute(stmt_refresh_tokens)
    refresh_token_db = result.unique().scalar_one_or_none()
    return refresh_token_db


@pytest.mark.asyncio
async def test_account_register_fields(client, db):
    email = "testtest1112111@gmail.com"
    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "Qwerty1221!"})
    assert response.status_code == 201
    decode_response = json.loads(response.content.decode())
    assert "email" in decode_response
    assert "activation_token" in decode_response

    stmt = select(User)
    result = await db.execute(stmt)
    new_test_user = result.unique().scalar_one_or_none()
    assert new_test_user.email == email

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "Qwerty1221"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should consist one of these symbols {'/.!&?,'}"

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "Qwertysasd/"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should consist at least one digit"

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "Qwerty"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should be not shorter than 8 characters"

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "123124124324/"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should consist at least one upper-case letter"

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "qeqwetqyu4/"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should consist at least one upper-case letter"

    response = await client.post(f"{account_prefix}register/", json={"email": email, "password": "TESTTEST1/"})
    assert response.status_code == 400
    assert json.loads(response.content.decode())["detail"] == "Password should consist at least one lower-case letter"



@pytest.mark.asyncio
async def test_account_activate(client, db):
    email = "testtest11111211@gmail.com"
    password = "Qwerty1221!"
    register_response = await client.post(f"{account_prefix}register/", json={"email": email, "password": password})
    json_content = json.loads(register_response.content.decode())
    activate_response = await client.post(f"{account_prefix}activate/", json=json_content)
    assert activate_response.status_code == 200

    stmt = select(User)
    result = await db.execute(stmt)
    test_user = result.unique().scalar_one_or_none()
    assert test_user.is_active == True


@pytest.mark.asyncio
async def test_account_login(client, db, create_user):
    email = "testtest1112111@gmail.com"
    password = "Testtest1221!"
    db_user = await create_user(
        email=email,
        password=password
    )
    response = await client.post("api/v1/accounts/login/", json={"email": email, "password": password})
    decode_response = json.loads(response.content.decode())
    assert decode_response["detail"] == "User account is not active"
    assert response.status_code == 403

    db_user.is_active = True
    await db.commit()
    response = await client.post("api/v1/accounts/login/", json={"email": email, "password": password})
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert "access_token" in decode_response
    assert "refresh_token" in decode_response

    refresh_token_db = await get_token_model_by_token(RefreshToken, decode_response["refresh_token"], db)
    assert refresh_token_db is not None


@pytest.mark.asyncio
async def test_account_reset_request_and_complete(client, db, create_user):
    email = "testtest1112111@gmail.com"
    password = "Testtest1221!"
    db_user = await create_user(
        email=email,
        password=password
    )
    response = await client.post("api/v1/accounts/reset-request/", json={"email": email})
    decode_response = json.loads(response.content.decode())
    assert decode_response["detail"] == "User account is not active"
    assert response.status_code == 403

    db_user.is_active = True
    await db.commit()
    response = await client.post("api/v1/accounts/reset-request/", json={"email": email})
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert "reset_token" in decode_response

    response_valid_token = await client.post("api/v1/accounts/reset-complete/", json={"reset_token": decode_response["reset_token"], "password": "NewPassword1221!"})
    decode_response = json.loads(response_valid_token.content.decode())
    assert response.status_code == 200
    assert decode_response == {'User password reset complete': True}

    response_invalid_token = await client.post("api/v1/accounts/reset-complete/", json={"reset_token": "false_token", "password": "NewPassword1221!"})
    decode_response = json.loads(response_invalid_token.content.decode())
    assert response_invalid_token.status_code == 400
    assert decode_response["detail"] == "Not enough segments"

    response_invalid_token = await client.post("api/v1/accounts/reset-complete/", json={"reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxfQ.SHRALNlfZeIZv30Zxkhmf74jOwgo8XAkD5MPky6eT0Y", "password": "NewPassword1221!"})
    decode_response = json.loads(response_invalid_token.content.decode())
    assert response_invalid_token.status_code == 400
    assert decode_response["detail"] == "Signature verification failed."


@pytest.mark.asyncio
async def test_account_logout(client, db, create_user):
    email = "testtest1112111@gmail.com"
    password = "Testtest1221!"
    db_user = await create_user(
        email=email,
        password=password
    )
    db_user.is_active = True
    await db.commit()

    response_login = await client.post("api/v1/accounts/login/", json={"email": email, "password": password})
    decode_response_login = json.loads(response_login.content.decode())

    response_logout = await client.post(
        "api/v1/accounts/logout/",
        headers={"Authorization": f"Bearer {decode_response_login["access_token"]}"},
        json={"refresh_token": decode_response_login["refresh_token"]}
    )
    assert response_logout.status_code == 200

    refresh_token_db = await get_token_model_by_token(RefreshToken, decode_response_login["refresh_token"], db)
    assert refresh_token_db is not None
