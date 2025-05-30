import os
import time

from app.util.send_runpod_webhook import send_runpod_webhook


def watchdog(timeout, job_id):
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
