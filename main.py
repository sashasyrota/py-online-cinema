from fastapi import FastAPI

from database.routes.profiles import profiles
from src.database.routes.accounts import accounts

app = FastAPI(

)

pref = "/api/v1"
app.include_router(accounts, prefix=pref)
app.include_router(profiles, prefix=pref)