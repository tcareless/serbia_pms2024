from celery import shared_task
import time

@shared_task
def long_running_task():
    """Simulate a long-running task."""
    for i in range(3):
        time.sleep(1)  # Simulating work
    return "Task Complete"


# celery -A pms worker --loglevel=info