from functools import wraps
from typing import Callable, Dict
from util import benchmark, notify

STEP_REGISTRY: Dict[str, Callable] = {}


def step(name: str):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapped(ctx):
            ctx.stage = name
            notify(ctx, name, "start")
            try:
                with benchmark(name):
                    result = fn(ctx)
                notify(ctx, name, "done")
                return result
            except Exception as e:
                ctx.status = "error"
                ctx.errors.append(f"{name}: {str(e)}")
                notify(ctx, name, "error", str(e))
                raise

        STEP_REGISTRY[name] = wrapped
        return wrapped

    return decorator
