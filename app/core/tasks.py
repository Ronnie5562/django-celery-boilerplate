# Sample Celery tasks for demonstration purposes
from __future__ import absolute_import, unicode_literals

import time
import random
from celery import shared_task
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


# Helper function for the long-running task
def process_item(item):
    """Process an individual item (simulated work)"""
    time.sleep(0.5)  # Simulate processing time
    return f"processed_{item}"


# Normal priority task (default queue)
@shared_task
def add(x, y):
    """Normal priority task example"""
    logger.info(f"Adding {x} + {y}")
    return x + y


# High priority task (explicit queue)
@shared_task(queue="high_priority")
def process_urgent_data(data):
    """High priority task example"""
    logger.warning(f"Processing urgent data: {data}")
    # Simulate urgent processing
    time.sleep(0.1)  # Less delay for high priority
    result = data.upper()
    logger.warning(f"Urgent task completed: {result}")
    return result


# Long-running task with progress tracking
@shared_task(bind=True)
def long_running_task(self, items):
    """Task with progress tracking"""
    total = len(items)
    results = []
    for i, item in enumerate(items, 1):
        # Update progress state
        self.update_state(
            state="PROGRESS", meta={"current": i, "total": total}
        )
        results.append(process_item(item))
    return {"result": results, "total_processed": total}


# Error handling task with retries
@shared_task(
    autoretry_for=(Exception,), retry_backoff=True,
    max_retries=3, retry_jitter=True
)
def unreliable_task(data):
    """Task with automatic retries"""
    if random.random() < 0.3:
        logger.error("Random failure occurred")
        raise Exception("Random failure")
    return f"processed_{data}"
