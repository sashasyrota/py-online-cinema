import datetime

from pydantic import BaseModel

from database.models.profiles import GenderEnum


class ProfileCreateRequestSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    avatar: str
    gender: GenderEnum | None
    date_of_birth: datetime.datetime | None
    info: str