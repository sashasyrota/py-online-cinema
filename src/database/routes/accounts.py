import datetime
from datetime import timezone

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import SECRET_KEY
from config.settings import ACTIVATION_TOKEN_EXPIRE_MINUTES
from database.models.accounts import User, UserGroup, UserGroupEnum, ActivationToken
from src.database.schemas.accounts import AccountCreationRequestSchema, AccountActivationRequestSchema
from src.database.session import get_db

accounts = APIRouter(
    prefix="/accounts"
)


@accounts.post(
    "/register/",
    status_code=200
)
async def create_account(
        account_schema: AccountCreationRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == account_schema.email)
    result_dublicate_user = await db.execute(stmt)
    if result_dublicate_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"User with {account_schema.email} is registered")

    db_user = User(
        email = str(account_schema.email),
        group_id=1
    )
    db_user.password = account_schema.password
    db.add(db_user)
    await db.flush()
    db_activation_token = ActivationToken(
        user_id=db_user.id,
        token=SECRET_KEY,
        expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=ACTIVATION_TOKEN_EXPIRE_MINUTES)
    )
    db.add(db_activation_token)
    await db.commit()
    return {"email": account_schema.email, "activation_token": db_activation_token.token}


@accounts.post(
    "/activate/",
    status_code=200
)
async def activate_account(
        account_schema: AccountActivationRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    stmt = select(ActivationToken).filter_by(token=account_schema.activation_token)
    result = await db.execute(stmt)
    db_activation_token = result.unique().scalar_one_or_none()

    if db_activation_token:
        if db_activation_token.expires_at >= datetime.datetime.now(timezone.utc):
            db_user = db_activation_token.user
            if db_user.email == account_schema.email:
                try:
                    db_user.is_active = True
                    await db.delete(db_activation_token)
                    await db.commit()
                except Exception as exc:
                    await db.rollback()
                    raise HTTPException(status_code=500, detail=str(exc))
                return {"User activated": True}
            raise HTTPException(status_code=400, detail="Incorrect email")
    raise HTTPException(status_code=400, detail="Invalid activation token or user already activated")

