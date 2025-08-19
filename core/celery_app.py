from celery import Celery
from core.config import settings

celery = Celery("balancecore", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery.task(name="health.ping")
def ping():
    return "pong"