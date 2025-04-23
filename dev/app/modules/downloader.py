import yt_dlp as youtube_dl
import os
from typing import Dict, Union

def download_video(url: str, output_dir: str = "downloads") -> Dict[str, Union[str, int, float]]:
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

        return {
            "status": "success",
            "path": ydl.prepare_filename(info_dict),
            "metadata": {
                "title": info_dict.get('title', ''),
                "duration": info_dict.get('duration', 0),
                "resolution": f"{info_dict.get('width', 0)}x{info_dict.get('height', 0)}",
                "view_count": info_dict.get('view_count', 0),
                "upload_date": info_dict.get('upload_date', '')
            }
        }
