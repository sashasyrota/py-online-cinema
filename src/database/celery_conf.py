from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://localhost:6379')

app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.expired_tokens',
        'schedule': crontab(hour=7)
    },
}
app.conf.timezone = 'UTC'