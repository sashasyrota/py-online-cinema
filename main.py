from fastapi import FastAPI

from database.routes.movies import movies
from database.routes.orders import orders
from database.routes.payments import payments
from database.routes.shopping_carts import carts
from src.database.routes.accounts import accounts

app = FastAPI(

)

pref = "/api/v1"
app.include_router(accounts, prefix=pref)
app.include_router(movies, prefix=pref)
app.include_router(carts, prefix=pref)
app.include_router(orders, prefix=pref)
app.include_router(payments, prefix=pref)