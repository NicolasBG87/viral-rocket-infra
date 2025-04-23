import time
from contextlib import contextmanager
from app.logger import logger


@contextmanager
def benchmark(name: str):
    start = time.time()
    logger.info(f"⏱️  Starting: {name}")
    yield
    end = time.time()
    elapsed = end - start
    logger.info(f"✅ Finished: {name} in {elapsed:.2f} seconds")
