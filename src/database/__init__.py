import os
from src.database.celery_conf import app

environment = os.getenv("ENVIRONMENT", "developing")


if environment == "developing":
    from src.database.session import get_async_db, get_sync_db
    from src.database.session import SyncSessionLocal

if environment == "testing":
    from src.database.session import (
        get_sqlite_async_db as get_async_db,
        get_sqlite_sync_db as get_sync_db,
    )
    from src.database.session import SyncSqliteSessionLocal as SyncSessionLocal

