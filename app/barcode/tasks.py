from celery import shared_task
import time

@shared_task
def test_task(test):
    time.sleep(10)

