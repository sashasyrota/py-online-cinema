from pydantic import BaseModel, EmailStr, field_validator, model_validator

from config.validators.accounts import validate_password


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