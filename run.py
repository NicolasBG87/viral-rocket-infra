import os

from app.logger import logger
from app.main import main
from app.user_enhanced import user_enhanced

if __name__ == "__main__":
    is_dev = os.getenv("IS_DEV", "false").lower() == "true"
    job_id = os.getenv("JOB_ID")
    video_url = os.getenv("INPUT_URL")
    is_user_enhanced = os.getenv("IS_USER_ENHANCED", "false").lower() == "true"

    if not is_user_enhanced:
        main(job_id, video_url, is_dev)
    else:
        user_enhanced(job_id, is_dev)

    logger.info("🏁 All done! Shutting down.")
