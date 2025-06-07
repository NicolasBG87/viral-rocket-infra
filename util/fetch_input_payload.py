import os
import json
import requests
from typing import cast

from pipeline.context import InputPayload


def fetch_input_payload(job_id: str, is_dev: bool) -> InputPayload:
    if is_dev:
        mock_path = "mock_inputs/job.json"
        if not os.path.exists(mock_path):
            raise FileNotFoundError(f"Mock input not found: {mock_path}")

        with open(mock_path, "r") as f:
            payload = json.load(f)

        return cast(InputPayload, payload)

    # Fetch from real API
    base_api_url = os.getenv("WEBHOOK_URL")
    if not base_api_url:
        raise EnvironmentError("WEBHOOK_URL must be set")

    from urllib.parse import urljoin

    api_url = urljoin(base_api_url, "processing/runpod-get-payload")
    response = requests.get(f"{api_url}?job_id={job_id}")
    response.raise_for_status()

    data = response.json()
    payload = data.get("payload")

    if not payload:
        raise ValueError("Missing payload in response")

    return cast(InputPayload, payload)
