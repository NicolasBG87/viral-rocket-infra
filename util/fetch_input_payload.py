import requests
from typing import cast, Optional

from pipeline.context import InputPayload
from util import logger


def fetch_input_payload(job_id: str, base_api_url: str) -> Optional[InputPayload]:
    if not base_api_url:
        logger.error("No base api url provided")
        raise RuntimeError("No base api url provided")

    from urllib.parse import urljoin

    api_url = urljoin(base_api_url, "processing/runpod-get-payload")
    response = requests.get(f"{api_url}?job_id={job_id}")
    response.raise_for_status()

    data = response.json()
    payload = data.get("payload")

    if not payload:
        logger.error(f"No payload found for job {job_id}")
        raise RuntimeError("No payload found for job")

    return cast(InputPayload, payload)
