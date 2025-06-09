from typing import cast

from pipeline import step, JobContext
from modules.youtube.downloader import extract_video_info
from pipeline.context import VideoMetadata
from util import logger


@step("download")
def run(ctx: JobContext):
    result = extract_video_info(
        url=ctx.input.get("video_url"),
        output_dir=ctx.output_dir,
    )

    info = result["info"]

    ctx.output["video_metadata"] = cast(VideoMetadata, {
        "url": ctx.input.get("video_url"),
        "title": info.get("title"),
        "duration": info.get("duration"),
        "resolution": info.get("resolution"),
        "width": info.get("width"),
        "height": info.get("height"),
        "size": info.get('filesize', 0),
        "format": info.get('format', ''),
        "thumbnailUrl": info.get("thumbnail"),
        "view_count": info.get("view_count") or 0,
        "upload_date": info.get('upload_date', ''),
        "description": info.get("description"),
        "transcript": result.get("captions"),
        "tags": info.get("tags") or [],
        "channel": info.get("channel") or "",
        "chapters": result.get("chapters") or [],
        "path": result.get("path") or "",
    })

    logger.info(f"✅ Video downloaded and metadata extracted")
