import os
import sys

import requests

from app.logger import logger
from urllib.parse import urljoin

from app.util.shutdown_pod import shutdown_pod


def send_runpod_webhook(job_id, job_payload, video=None, launch=None):
    base_api_url = os.getenv("WEBHOOK_URL")
    api_url = urljoin(base_api_url, "processing/runpod-callback")
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
        if "localhost" in api_url or isinstance(e.__cause__, socket.gaierror):
            logger.warning("Shutting down pod due to invalid callback URL.")
            shutdown_pod()
            sys.exit(0)

        logger.info(f"❌ Webhook failed: {e}")
        raise RuntimeError(f"Webhook failed: {e}")
