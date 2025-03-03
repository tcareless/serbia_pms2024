from celery import shared_task
import time

@shared_task
def long_running_task():
    """Simulate a long-running task."""
    for i in range(5):
        time.sleep(2)  # Simulating work
    return "Task Complete"
