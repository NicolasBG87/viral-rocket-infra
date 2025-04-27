import time
from contextlib import contextmanager
from app.logger import logger

benchmark_results = {}


@contextmanager
def benchmark(name: str):
    start = time.time()
    logger.info(f"⏱️  Starting: {name}")

    try:
        yield
    finally:
        end = time.time()
        elapsed = end - start
        benchmark_results[name] = elapsed * 1000
        logger.info(f"✅ Finished: {name} in {elapsed:.2f} seconds")
