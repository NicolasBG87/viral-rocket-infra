import time
import random
from openai import OpenAI
from util import logger

def safe_chat_completion(client: OpenAI, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            is_rate_limit = hasattr(e, "status_code") and e.status_code == 429
            base_wait = 10 * (2 ** max(attempt - 1, 0))
            wait_time = min(base_wait + random.uniform(0, 1), 120)

            if is_rate_limit:
                logger.warning(f"[429] Rate limited. Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"OpenAI call failed: {e}")
                raise

    raise RuntimeError("Max retries exceeded for OpenAI call")
