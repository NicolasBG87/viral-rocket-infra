import os
import time

from app.util.send_runpod_webhook import send_runpod_webhook


def watchdog(timeout=1800, job_id):  # e.g. 30 mins
    time.sleep(timeout)
    send_runpod_webhook(
        job_id,
        {
            "status": 'failed',
            "stage": 'failed',
            "error": "Pod timed out"
        },
    )
    os._exit(1)