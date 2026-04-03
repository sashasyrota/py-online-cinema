import datetime
from fastapi import HTTPException
from fastapi.security import APIKeyHeader

from jose import JWTError, jwt

SECRET_KEY = "ygf5zQAC9TEpQ1SAsm5dft0jrwcHBZ1o"
ALGORITHM = "HS256"
authorization_header = APIKeyHeader(name="Authorization", auto_error=False)


def create_token(data: dict, expires_delta: datetime.timedelta = 15):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as er:
        raise HTTPException(status_code=400, detail=str(er))

