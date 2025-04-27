import os

import requests

from app.logger import logger


def send_runpod_webhook(job_id, job_payload, video=None, launch=None):
    api_url = os.getenv("WEBHOOK_URL")
    is_dev = os.getenv("IS_DEV", "false").lower() == "true"

    if is_dev:
        logger.info("Skipping Webhook for dev job")
        return

    payload = {
        "job_id": job_id,
        "payload": {
            "job": job_payload,
            "video": video,
            "launch": launch,
        }
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        logger.info(f"✅ Webhook sent: {job_payload['stage']}")
    except Exception as e:
        logger.info(f"❌ Webhook failed: {e}")
