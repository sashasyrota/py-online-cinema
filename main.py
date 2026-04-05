from fastapi import FastAPI
from src.database.routes.accounts import accounts

app = FastAPI(

)

pref = "/api/v1"
app.include_router(accounts, prefix=pref)