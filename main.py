from fastapi import FastAPI

from src.database.routes.movies import movies
from src.database.routes.orders import orders
from src.database.routes.payments import payments
from src.database.routes.shopping_carts import carts
from src.database.routes.accounts import accounts

app = FastAPI(

)

pref = "/api/v1"
app.include_router(accounts, prefix=pref)
app.include_router(movies, prefix=pref)
app.include_router(carts, prefix=pref)
app.include_router(orders, prefix=pref)
app.include_router(payments, prefix=pref)