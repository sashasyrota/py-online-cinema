from celery.schedules import crontab

from src.database import app

app.conf.beat_schedule = {
    "delete_every_day_in_7_00_utc": {
        "task": "src.tasks.expired_tokens",
        "schedule": crontab(hour=7),
    },
}
app.conf.timezone = "UTC"
