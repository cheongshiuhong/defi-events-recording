import os
from celery import Celery


BROKER_URI = os.environ.get("BROKER_URI", "redis://redis:6379")


worker = Celery(
    "worker",
    broker=BROKER_URI,
    backend=BROKER_URI,
    include=["src.historical.tasks.batch.task"],
)
