import sys

import requests

from app.logger import logger
from urllib.parse import urljoin


def send_runpod_webhook(base_api_url, job_id, job_payload, video=None, launch=None):
    api_url = urljoin(base_api_url, "processing/runpod-callback")
    is_dev = False

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
        sys.exit(0)
