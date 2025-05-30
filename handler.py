import runpod
import os
from app.main import main
from app.user_enhanced import user_enhanced

output_dir = "output"


def handler(job):
    job_input = job["input"]
    is_dev = False
    job_id = job_input["job_id"]
    video_url = job_input["video_url"]
    game_title = job_input["game_title"]
    is_user_enhanced = job_input["is_user_enhanced"].lower() == "true"
    duration_limit = job_input["duration_limit"]
    quality_limit = job_input["quality_limit"]
    base_api_url = job_input["webhook_url"]

    if not is_user_enhanced:
        result = main(output_dir, job_id, video_url, game_title, duration_limit, quality_limit, is_dev, base_api_url)
    else:
        result = user_enhanced(output_dir, job_id, game_title, is_dev, base_api_url)

    return result


runpod.serverless.start({"handler": handler})
