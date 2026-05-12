import asyncio
import datetime
import typing

from fastapi import Depends
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from src.database.models.accounts import ActivationToken, PasswordResetToken, RefreshToken
from src.database.session import get_async_db, get_sync_db, SyncSessionLocal
from src.database import app


def select_token(session: Session):
    for token in [ActivationToken, PasswordResetToken, RefreshToken]:
        stmt = delete(token).filter(token.expires_at < datetime.datetime.now(datetime.UTC))
        session.execute(stmt)
        session.commit()


@app.task
def expired_tokens():
    with SyncSessionLocal() as session:
        try:
            select_token(session)
        except Exception as error:
            print(str(error))
