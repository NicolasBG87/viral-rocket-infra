import time
from contextlib import contextmanager
from util.logger import logger

benchmark_results = {}


@contextmanager
def benchmark(name: str):
    start = time.time()
    logger.info(f"⏱️  Starting: {name}")
    try:
        yield
    finally:
        end = time.time()
        elapsed = round(end - start, 2)
        benchmark_results[name] = elapsed
        logger.info(f"✅ Finished: {name} in {elapsed:.2f}s")
