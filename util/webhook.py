import sys

import requests
from urllib.parse import urljoin

from util.logger import logger


def notify(ctx, stage: str, status: str, error: str = None):
    base_url = ctx.webhook_url
    if not base_url:
        logger.warning("No WEBHOOK_URL set.")
        raise RuntimeError("No WEBHOOK_URL set.")

    url = urljoin(base_url, "processing/runpod-callback")

    payload = {
        "job_id": ctx.job_id,
        "stage": stage,
        "status": status,
        "error": error,
        "payload": {
            "video": ctx.output.get("video_metadata"),
            "launch": {
                "title": ctx.output.get("title"),
                "description": ctx.output.get("description"),
                "chapters": ctx.output.get("chapters"),
                "summary": ctx.output.get("summary"),
            },
        }
    }

    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        logger.info(f"📡 Webhook sent: {stage}:{status}")
    except Exception as e:
        logger.warning(f"⚠️ Webhook failed: {e}")
        sys.exit(0)
