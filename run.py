import os

from app.logger import logger
from app.main import main
from app.user_enhanced import user_enhanced

output_dir = "output"

if __name__ == "__main__":
    is_dev = os.getenv("IS_DEV", "false").lower() == "true"
    job_id = os.getenv("JOB_ID")
    video_url = os.getenv("VIDEO_URL")
    game_title = os.getenv("GAME_TITLE")
    is_user_enhanced = os.getenv("IS_USER_ENHANCED", "false").lower() == "true"
    duration_limit = os.getenv("DURATION_LIMIT")
    quality_limit = os.getenv("QUALITY_LIMIT")

    if not is_user_enhanced:
        main(output_dir, job_id, video_url, game_title, duration_limit, quality_limit, is_dev)
    else:
        user_enhanced(output_dir, job_id, game_title, is_dev)

    logger.info("🏁 All done! Shutting down.")
