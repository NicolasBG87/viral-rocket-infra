import time
from openai import OpenAI
import random
from app.logger import logger


def safe_chat_completion(client, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except OpenAI.RateLimitError as e:
            base_wait = 10 * (2 ** (attempt - 1)) if attempt > 0 else 10
            wait_time = min(base_wait + random.uniform(0, 1), 120)
            logger.info(f"[429] Rate limited. Retrying in {wait_time:.2f}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            raise RuntimeError(f"OpenAI call failed: {e}")
    raise RuntimeError("Max retries exceeded")
