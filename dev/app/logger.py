import time

from loguru import logger

logger.add("debug.log", rotation="500 KB", backtrace=True, diagnose=True)


def benchmark_start(message: str) -> float:
    start = time.time()
    print(message)
    return start


def benchmark_stop(message: str, start: float) -> None:
    end = time.time()
    print(f"{message} took {end - start:.2f} sec")
