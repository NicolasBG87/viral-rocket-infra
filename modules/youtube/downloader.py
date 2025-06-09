import os
import yt_dlp as youtube_dl
import requests
from typing import Dict, List, Union

from util import logger


def extract_video_info(url: str, output_dir: str) -> Dict:
    os.makedirs(output_dir, exist_ok=True)
    path = None

    # 1. Extract info without downloading
    ydl_opts_info = _get_options(output_dir, download=False)
    with youtube_dl.YoutubeDL(ydl_opts_info) as ydl:
        info = ydl.extract_info(url, download=False)

    captions = fetch_captions(info)
    chapters = extract_chapters(info)

    # 2. Decide whether to download audio or skip
    if not captions:
        ydl_opts_audio = _get_options(output_dir, download=True)
        with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)

    return {
        "info": info,
        "path": path,
        "captions": captions,
        "chapters": chapters,
    }


def _get_options(output_dir: str, download: bool) -> Dict:
    format_str = (
        'bestvideo[ext=mp4][vcodec^=h264][vcodec!=av01]+bestaudio[ext=m4a]/bestvideo+bestaudio'
        if not download else
        'bestaudio/best'
    )
    return {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': format_str,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'nocheckcertificate': True,
        'prefer-insecure': True,
        'quiet': True,
        'noprogress': True,
        'cookiefile': os.path.join('cookies', 'cookies.txt'),
    }


def fetch_captions(info_dict) -> Union[Dict, None]:
    preferred_langs = ["en", "en-US", "en-GB"]
    subtitles = info_dict.get("subtitles", {})
    auto_captions = info_dict.get("automatic_captions", {})

    caption_sources = []
    for lang in preferred_langs:
        if lang in subtitles:
            caption_sources.append(("User", subtitles[lang]))
    for lang in preferred_langs:
        if lang in auto_captions:
            caption_sources.append(("Auto", auto_captions[lang]))

    for source_name, tracks in caption_sources:
        if not tracks:
            continue
        try:
            caption_url = tracks[0]["url"]
            response = requests.get(caption_url)
            data = response.json()

            segments = []
            full_text = []

            for event in data.get("events", []):
                if "segs" not in event:
                    continue
                text = "".join(seg["utf8"] for seg in event["segs"]).strip()
                start = event.get("tStartMs", 0) / 1000
                duration = event.get("dDurationMs", 0) / 1000
                end = start + duration

                if text:
                    segments.append({"start": start, "end": end, "text": text})
                    full_text.append(text)

            return {
                "text": " ".join(full_text),
                "segments": segments,
                "duration": segments[-1]["end"] if segments else info_dict.get("duration", 0),
                "source": source_name
            }

        except Exception as e:
            logger.error(f"⚠️ Failed to fetch {source_name} captions: {e}")

    return None


def extract_chapters(info_dict) -> Union[List[Dict], None]:
    chapters = info_dict.get("chapters")
    if not chapters:
        return None
    return [
        {
            "title": ch.get("title", f"Chapter {i + 1}"),
            "start_time": ch.get("start_time", 0),
            "end_time": ch.get("end_time", 0),
        } for i, ch in enumerate(chapters)
    ]
