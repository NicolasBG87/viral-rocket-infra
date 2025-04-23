import os
import requests
from typing import Dict, Union
import yt_dlp as youtube_dl


def download_video(url: str, output_dir: str = "input") -> Dict[str, Union[str, int, float]]:
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = _get_download_options(output_dir)

    try:
        return _perform_download(url, ydl_opts)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "metadata": None,
            "path": None
        }


def _get_download_options(output_dir: str) -> Dict:
    return {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': (
            'bestvideo[ext=mp4][vcodec^=h264][vcodec!=av01]+bestaudio[ext=m4a]/'
            'bestvideo[ext=webm][vcodec^=vp9][vcodec!=av01]+bestaudio[ext=m4a]/'
            'bestvideo[ext=mp4][vcodec!=av01]+bestaudio/best'
        ),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'verbose': False,
    }


def _perform_download(url: str, ydl_opts: Dict) -> Dict:
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        transcript_data = _fetch_youtube_auto_captions(info_dict)

        return {
            "status": "success",
            "path": ydl.prepare_filename(info_dict),
            "transcript": transcript_data,
            "metadata": {
                "title": info_dict.get('title', ''),
                "duration": info_dict.get('duration', 0),
                "resolution": f"{info_dict.get('width', 0)}x{info_dict.get('height', 0)}",
                "view_count": info_dict.get('view_count', 0),
                "upload_date": info_dict.get('upload_date', '')
            }
        }


def _fetch_youtube_auto_captions(info_dict) -> Union[Dict, None]:
    captions = info_dict.get("automatic_captions") or {}

    # Try to fetch English auto-captions
    if "en" in captions:
        try:
            caption_url = captions["en"][0]["url"]
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
                "duration": segments[-1]["end"] if segments else info_dict.get("duration", 0)
            }

        except Exception as e:
            print(f"⚠️ Failed to download YT captions: {e}")

    return None
