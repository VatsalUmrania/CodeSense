from celery import shared_task
import time

@shared_task(name="test_celery_task")
def test_celery_task(word: str):
    print(f"Processing task for: {word}")
    time.sleep(1) 
    return f"{word[::-1]}"