from app.modules.downloader import download_video
from app.modules.transcript_generator import TranscriptGenerator
from app.util.timer import benchmark


def main():
    with benchmark("🚀 Video processing pipeline"):
        # 1. Download
        with benchmark("Downloading video"):
            url = "https://www.youtube.com/watch?v=D_5r45LipuM"
            download_result = download_video(url)
            video_path = download_result["path"]

        # 2. Transcribe
        with benchmark("Transcript Generation"):
            tg = TranscriptGenerator()
            tg.transcribe(video_path, "output")
