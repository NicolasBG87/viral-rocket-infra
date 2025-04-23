import subprocess
import json
from app.logger import logger


def get_video_duration(file_path: str) -> float:
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        output = json.loads(result.stdout)
        duration = float(output['format']['duration'])
        logger.info(f"📽️ Video duration: {duration:.2f} seconds")
        return duration

    except Exception as e:
        logger.error(f"❌ Failed to get video duration for {file_path}: {e}")
        return 0.0
