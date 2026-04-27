import os
environment = os.getenv("ENVIRONMENT", "developing")

if environment == "developing":
    from src.database.session import get_async_db, get_sync_db

if environment == "testing":
    from src.database.session import get_sqlite_async_db as get_async_db, get_sync_db