from app.logger import logger
from app.util.save_output import save_metadata, save_transcript
from app.util.timer import benchmark
from app.util.cleanup import clean_up
from app.util.video import get_video_duration
from app.modules.downloader import download_video
from app.modules.transcript_generator import TranscriptGenerator
from app.modules.transcript_scorer import TranscriptScorer
from app.modules.metadata_generator import MetadataGenerator

output_dir = 'output'


def main():
    with benchmark("🚀 Video processing pipeline"):
        # 1. Download
        with benchmark("Downloading video"):
            url = "https://www.youtube.com/watch?v=W0wlKMhJOPY"
            download_result = download_video(url)
            video_path = download_result["path"]
            video_duration = get_video_duration(video_path)
            yt_transcript = download_result.get("transcript")

        # 2. Transcribe
        with benchmark("Transcript Generation"):
            if yt_transcript:
                logger.info("✅ Using YouTube auto transcript.")
                transcript_data = yt_transcript
            else:
                logger.info("🌀 No YT transcript — running Whisper...")
                tg = TranscriptGenerator()
                transcript_data = tg.transcribe(video_path, output_dir)

            save_transcript(transcript_data, output_dir)

        # 3. Transcript Scoring
        with benchmark("Transcript Scoring"):
            ts = TranscriptScorer(transcript_data, video_duration)
            score = ts.score()

            if score >= 0.5:
                logger.info("👍 Transcript is rich — proceeding with GPT metadata generation.")
                mg = MetadataGenerator()
                result = mg.generate(transcript_data.get("text"))
                save_metadata(result, output_dir)

            else:
                logger.warning("⚠️ Transcript is weak — triggering fallback to multimodal analysis.")

    # Clean-up
    # clean_up(output_dir)
