import os

import requests


def send_runpod_webhook(job_id, job_payload, video=None, launch=None):
    api_url = os.getenv("WEBHOOK_URL")
    is_dev = os.getenv("IS_DEV", "false").lower() == "true"

    if is_dev:
        print("Skipping Webhook for dev job")
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
        print(f"✅ Webhook sent: {job_payload['stage']}")
    except Exception as e:
        print(f"❌ Webhook failed: {e}")
