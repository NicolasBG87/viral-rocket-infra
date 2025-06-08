import os
import json

import requests

from pipeline import JobContext, step
from util import logger


@step("save_output")
def run(ctx: JobContext):
    if not ctx.is_dev:
        return

    output_dir = ctx.output_dir
    os.makedirs(output_dir, exist_ok=True)

    output = ctx.output
    video_metadata = output.get("video_metadata")
    transcript = video_metadata.get("transcript")

    # Save metadata
    if video_metadata:
        with open(os.path.join(output_dir, "video_metadata.json"), "w") as f:
            json.dump(video_metadata, f, indent=2)
        logger.info("💾 Video Metadata saved")

    # if ctx.chapters:
    #     with open(os.path.join(output_dir, "chapters.json"), "w") as f:
    #         json.dump(ctx.chapters, f, indent=2)
    #     logger.info("💾 chapters saved")

    # Save transcript
    if transcript:
        with open(os.path.join(output_dir, "transcript.txt"), "w") as f:
            f.write(transcript.get("text", ""))
        with open(os.path.join(output_dir, "transcript.json"), "w") as f:
            json.dump(transcript, f, indent=2)
        logger.info("💾 Transcript saved")

    # Save score if available
    if "transcript_score" in video_metadata:
        with open(os.path.join(output_dir, "score.txt"), "w") as f:
            f.write(str(video_metadata["transcript_score"]))
        logger.info("📈 Score saved")

    # Save metadata
    output_without_video = dict(output)
    output_without_video.pop("video_metadata", None)
    if output_without_video:
        with open(os.path.join(output_dir, "generated_metadata.json"), "w") as f:
            json.dump(output_without_video, f, indent=2)
        logger.info("💾 Video Metadata saved")

    thumbnail_url = output.get("thumbnail_url")
    if thumbnail_url:
        try:
            response = requests.get(thumbnail_url)
            response.raise_for_status()
            with open(os.path.join(output_dir, "thumbnail.jpg"), "wb") as f:
                f.write(response.content)
            logger.info("🖼️ Thumbnail saved locally")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save thumbnail: {e}")
