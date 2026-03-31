import datetime
from datetime import timezone

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import SECRET_KEY, create_token, decode_token
from config.security.password import verify_password
from config.settings import ACTIVATION_TOKEN_EXPIRE_MINUTES, RESET_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES, \
    ACCESS_TOKEN_EXPIRE_MINUTES
from database.models.accounts import User, UserGroup, UserGroupEnum, ActivationToken, PasswordResetToken, RefreshToken
from database.schemas.accounts import AccountResendActivationLinkRequestSchema, AccountResetPasswordRequestSchema, \
    AccountResetPasswordCompleteSchema, AccountLoginSchema, RefreshTokenSchema
from src.database.schemas.accounts import AccountCreationRequestSchema, AccountActivationRequestSchema
from src.database.session import get_db

accounts = APIRouter(
    prefix="/accounts"
)



async def get_user_by_email(email: str, db: AsyncSession):
    stmt = select(User).filter_by(email=email)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    return db_user


@accounts.post(
    "/register/",
    status_code=201
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

    token = create_token(
        data={"user_id": db_user.id},
        expires_delta=datetime.timedelta(minutes=ACTIVATION_TOKEN_EXPIRE_MINUTES)
    )
    db_activation_token = ActivationToken(
        user_id=db_user.id,
        token=token,
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
    decode_token(account_schema.activation_token)

    stmt = select(ActivationToken).filter_by(token=account_schema.activation_token)
    result = await db.execute(stmt)
    db_activation_token = result.unique().scalar_one_or_none()

    if db_activation_token:
        user = db_activation_token.user
        if not user.is_active:
            try:
                db_activation_token.user.is_active = True
                await db.delete(db_activation_token)
                await db.commit()
                return {"User activated": True}
            except Exception as exc:
                await db.rollback()
                raise HTTPException(status_code=500, detail=str(exc))
        raise HTTPException(status_code=400, detail="User already activated")
    raise HTTPException(status_code=404, detail="User with this activation token not found")


@accounts.post(
    "/resend/",
    status_code=200
)
async def resend_activation_link(
        account_schema: AccountResendActivationLinkRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_email(str(account_schema.email), db=db)

    if db_user:
        token = create_token(
            data={"user_id": db_user.id},
            expires_delta=datetime.timedelta(minutes=ACTIVATION_TOKEN_EXPIRE_MINUTES)
        )
        db_activation_token = ActivationToken(
            user_id=db_user.id,
            token=token,
            expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=ACTIVATION_TOKEN_EXPIRE_MINUTES)
        )
        db.add(db_activation_token)
        await db.commit()
        return {"activation_token": token}
    raise HTTPException(status_code=400, detail=f"User with {account_schema.email} not registered")


@accounts.post(
    "/reset-request/",
    status_code=200
)
async def reset_request_password(
        account_schema: AccountResetPasswordRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_email(str(account_schema.email), db=db)
    if db_user:
        reset_token_db = db_user.password_reset_token
        try:
            if reset_token_db:
                await db.delete(reset_token_db)
                await db.flush()
            new_reset_token = create_token(
                data={"user_id": db_user.id},
                expires_delta=datetime.timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
            )
            new_reset_token_db = PasswordResetToken(
                user_id=db_user.id,
                token=new_reset_token,
                expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                    minutes=RESET_TOKEN_EXPIRE_MINUTES)
            )
            reset_token_db = new_reset_token_db
            db.add(reset_token_db)
            await db.commit()
            return {"reset_token": new_reset_token}
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))


@accounts.post("/reset-complete/", status_code=200)
async def reset_complete_password(
        account_schema: AccountResetPasswordCompleteSchema,
        db: AsyncSession = Depends(get_db)
):
    decode_token(account_schema.reset_token)
    stmt = select(PasswordResetToken).filter_by(token=account_schema.reset_token)
    result = await db.execute(stmt)
    db_reset_token = result.scalar_one_or_none()
    if db_reset_token:
        db_user = db_reset_token.user
        try:
            db_user.password = account_schema.password
            await db.delete(db_reset_token)
            await db.commit()
            return {"User password reset complete": True}
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=400, detail="Invalid reset token")


@accounts.post("/login/", status_code=200)
async def login_account(
        account_schema: AccountLoginSchema,
        db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_email(str(account_schema.email), db)
    if db_user:
        if verify_password(account_schema.password, str(db_user.hashed_password)):
            try:
                refresh_token = create_token(
                    data={
                        "type": "refresh",
                        "user_id": db_user.id,
                    },
                    expires_delta = datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
                )
                refresh_token_db = RefreshToken(
                    user_id=db_user.id,
                    token=refresh_token,
                    expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(
                            minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
                )
                db.add(refresh_token_db)
                await db.commit()

                access_token = create_token(
                    data={
                        "type": "access",
                        "user_id": db_user.id
                    },
                    expires_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                )
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=400, detail="Email or password is wrong")


@accounts.post("/refresh/", status_code=200)
async def refresh_token(
        account_schema: RefreshTokenSchema,
        db: AsyncSession = Depends(get_db)
):
    refresh_token = account_schema.refresh_token
    decode_token(refresh_token)
    stmt = select(RefreshToken).filter_by(token=refresh_token)
    result = await db.execute(stmt)
    refresh_token_db = result.scalar_one_or_none()
    if refresh_token_db:
        access_token = create_token(
            data={
                "type": "access",
                "user_id": refresh_token_db.user_id
            },
            expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token}
    raise HTTPException(status_code=400, detail="Invalid refresh token")
