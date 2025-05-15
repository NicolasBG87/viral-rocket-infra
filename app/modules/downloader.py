import os
import requests
from typing import Dict, Union
import yt_dlp as youtube_dl


def download_video(url: str, download: bool, output_dir: str = "input") -> Dict[
    str, Union[str, int, float, Dict[str, Union[str, int, float]]]]:
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = _get_download_options(output_dir)

    try:
        return _perform_download(url, ydl_opts, download)
    except Exception as e:
        raise RuntimeError(f"Error: {e}")


def _get_download_options(output_dir: str) -> Dict:
    return {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': (
            'bestvideo[ext=mp4][vcodec^=h264][vcodec!=av01][height<=720]+bestaudio[ext=m4a]/'
            'bestvideo[ext=webm][vcodec^=vp9][vcodec!=av01][height<=720]+bestaudio[ext=m4a]/'
            'bestvideo[ext=mp4][vcodec!=av01][height<=720]+bestaudio/best[height<=720]/best'
            'bestvideo[ext=mp4][vcodec^=h264][vcodec!=av01]+bestaudio[ext=m4a]/'
            'bestvideo[ext=webm][vcodec^=vp9][vcodec!=av01]+bestaudio[ext=m4a]/'
            'bestvideo[ext=mp4][vcodec!=av01]+bestaudio/best'
        ),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'noprogress': True,
        'progress_hooks': [_progress_hook],
    }


def _perform_download(url: str, ydl_opts: Dict, download: bool) -> Dict:
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=download)
        transcript_data = _fetch_captions(info_dict)

        return {
            "status": "success",
            "path": ydl.prepare_filename(info_dict),
            "transcript": transcript_data,
            "metadata": {
                "url": url,
                "title": info_dict.get('title', ''),
                "duration": info_dict.get('duration', 0),
                "resolution": f"{info_dict.get('width', 0)}x{info_dict.get('height', 0)}",
                "width": info_dict.get('width', 0),
                "height": info_dict.get('height', 0),
                "size": info_dict.get('filesize', 0),
                "format": info_dict.get('format', ''),
                "thumbnailUrl": info_dict.get('thumbnail', ''),
                "view_count": info_dict.get('view_count', 0),
                "upload_date": info_dict.get('upload_date', '')
            }
        }


def _fetch_captions(info_dict) -> Union[Dict, None]:
    preferred_langs = ["en", "en-US", "en-GB"]
    subtitles = info_dict.get("subtitles", {})
    auto_captions = info_dict.get("automatic_captions", {})

    # Create prioritized list of sources: first user-uploaded, then auto
    caption_sources = []
    for lang in preferred_langs:
        if lang in subtitles:
            caption_sources.append(("User", subtitles[lang]))
    for lang in preferred_langs:
        if lang in auto_captions:
            caption_sources.append(("Auto", auto_captions[lang]))

    # Attempt to fetch captions
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
            print(f"⚠️ Failed to fetch {source_name} captions: {e}")

    return None


def _progress_hook(e):
    print(f"⚠️ Failed to download: {e}")
    pass
