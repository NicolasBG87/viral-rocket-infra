from pipeline import step, JobContext
from util import logger

QUALITY_LIMITS = {
    "1080p": 1920,
    "4k": 3840,
    "Unlimited": float("inf"),
}


@step("check_limits")
def run(ctx: JobContext):
    try:
        duration_limit = int(ctx.input.get("duration_limit"))
    except (ValueError, TypeError):
        duration_limit = float("inf")

    quality_limit = ctx.input.get("quality_limit")
    width_limit = QUALITY_LIMITS.get(quality_limit, float("inf"))

    video_metadata = ctx.output.get("video_metadata")
    duration = video_metadata.get("duration") or 0
    width = video_metadata.get("width") or 0

    if duration > duration_limit or width > width_limit:
        logger.warning("🛑 Video exceeds allowed limits. Shutting down.")
        raise RuntimeError("Video exceeds allowed duration or resolution limits.")

    logger.info("📏 Video is within allowed duration and quality limits.")
