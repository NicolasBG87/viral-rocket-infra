from app.logger import logger
from app.util.timer import benchmark
from app.util.cleanup import clean_up
from app.util.video import get_video_duration
from app.modules.downloader import download_video
from app.modules.transcript_generator import TranscriptGenerator
from app.modules.transcript_scorer import TranscriptScorer

output_dir = 'output'


def main():
    with benchmark("🚀 Video processing pipeline"):
        # 1. Download
        with benchmark("Downloading video"):
            url = "https://www.youtube.com/watch?v=D_5r45LipuM"
            download_result = download_video(url)
            video_path = download_result["path"]
            video_duration = get_video_duration(video_path)

        # 2. Transcribe
        with benchmark("Transcript Generation"):
            tg = TranscriptGenerator()
            transcript_data = tg.transcribe(video_path, output_dir)

        with benchmark("Transcript Generation"):
            ts = TranscriptScorer(transcript_data, video_duration)
            score = ts.score()

            if score >= 0.5:
                logger.info("👍 Transcript is rich — proceeding with GPT metadata generation.")
            else:
                logger.warning("⚠️ Transcript is weak — triggering fallback to multimodal analysis.")

    # Clean-up
    clean_up(output_dir)
