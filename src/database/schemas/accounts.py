import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from config.validators.accounts import validate_password
from src.database.models.accounts import GenderEnum


class AccountCreationRequestSchema(BaseModel):
    email: EmailStr
    password: str

    @model_validator(mode="after")
    def validate_password(self):
        validate_password(self.password)
        return self


class AccountActivationRequestSchema(BaseModel):
    email: EmailStr
    activation_token: str


class AccountResendActivationLinkRequestSchema(BaseModel):
    email: EmailStr


class AccountResetPasswordRequestSchema(BaseModel):
    email: EmailStr


class AccountResetPasswordCompleteSchema(BaseModel):
    reset_token: str
    password: str

    @model_validator(mode="after")
    def validate_password(self):
        validate_password(self.password)
        return self


class AccountLoginSchema(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccountLogoutSchema(BaseModel):
    refresh_token: str


class ProfileCreateRequestSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    gender: GenderEnum | None
    date_of_birth: datetime.date | None
    info: str
    avatar: str
    user_id: int


class AccountChangeSchema(BaseModel):
    user_id: int
    group_id: int | None
    is_active: bool