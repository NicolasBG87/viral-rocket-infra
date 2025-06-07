import time

from util import shutdown_pod
from util.webhook import notify


def watchdog(timeout_seconds: int, ctx):
    time.sleep(timeout_seconds)
    notify(ctx, ctx.stage, "error", error="Pod timed out")
    shutdown_pod()
