import datetime
from typing import Annotated

from fastapi import Depends, Form, UploadFile, APIRouter, File
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header
from database.models.profiles import GenderEnum
from database.session import get_async_db


profiles = APIRouter(
    prefix="/profiles"
)


@profiles.post("/create_profile/")
async def create_profile(
        first_name: str = Form(None),
        last_name: str = Form(None),
        gender: GenderEnum = Form(None),
        date_of_birth: datetime.datetime = Form(None),
        info: str = Form(),
        avatar: UploadFile = File(),
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    v