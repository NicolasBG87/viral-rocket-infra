from app.logger import logger
from app.util.cleanup import clean_up
from app.util.save_output import save_metadata, save_transcript
from app.util.send_runpod_webhook import send_runpod_webhook
from app.util.shutdown_pod import shutdown_pod
from app.util.timer import benchmark, benchmark_results
from app.modules.downloader import download_video
from app.modules.transcript_generator import TranscriptGenerator
from app.modules.transcript_scorer import TranscriptScorer
from app.modules.metadata_generator import MetadataGenerator

QUALITY_LIMITS = {
    "1080p": 1920,
    "4k": 3840,
    "Unlimited": float('inf'),
}


def main(output_dir, job_id, video_url, game_title, duration_limit, quality_limit, is_dev):
    job_status = "queued"
    job_stage = "downloading"

    try:
        with benchmark("🚀 Video processing pipeline"):
            # 1. Download Transcript
            with benchmark("Downloading video transcript"):
                download_result = download_video(video_url, False)
                video_duration = download_result.get("metadata").get("duration")
                video_width = download_result.get("metadata").get("width")

                yt_transcript = download_result.get("transcript")
                job_status = "processing"
                job_stage = "downloading"

            send_runpod_webhook(
                job_id,
                {
                    "status": job_status,
                    "stage": job_stage,
                    "duration": benchmark_results["Downloading video transcript"]
                },
                video=download_result.get("metadata")
            )

            with benchmark("Checking video limits"):
                limit_reached = False
                width_limit = QUALITY_LIMITS.get(quality_limit, float('inf'))
                job_status = "processing"
                job_stage = "checking_limits"
                if video_duration > duration_limit or video_width > width_limit:
                    job_status = "limit_exceeded"
                    limit_reached = True
                    logger.info("🛑 Video exceeds allowed limits. Shutting down.")

            send_runpod_webhook(
                job_id,
                {
                    "status": job_status,
                    "stage": job_stage,
                    "duration": benchmark_results["Checking video limits"]
                },
                video=download_result.get("metadata")
            )

            if limit_reached:
                shutdown_pod()

            # 2. Transcribe
            with benchmark("Generating transcript"):
                job_status = "processing"
                job_stage = "transcribing"
                if yt_transcript:
                    logger.info("✅ Using YouTube transcript.")
                    transcript_data = yt_transcript
                else:
                    logger.info("🌀 No YT transcript — downloading raw video...")
                    download_result = download_video(video_url, True)
                    video_path = download_result["path"]
                    logger.info("🌀 Running Whisper...")
                    tg = TranscriptGenerator()
                    transcript_data = tg.transcribe(video_path)

            send_runpod_webhook(
                job_id,
                {
                    "status": job_status,
                    "stage": job_stage,
                    "duration": benchmark_results["Generating transcript"]
                },
            )

            # 3. Transcript Scoring
            with benchmark("Generating metadata"):
                ts = TranscriptScorer(transcript_data, video_duration)
                score = ts.score()

                if score >= 0.5:
                    logger.info("👍 Transcript is rich — proceeding with GPT metadata generation.")
                    mg = MetadataGenerator()
                    result = mg.generate(game_title, transcript_data.get("text"))
                    launch_status = "complete"
                    job_status = "completed"
                    job_stage = "done"

                else:
                    logger.warning("⚠️ Transcript is weak — triggering fallback to multimodal analysis.")
                    result = {
                        "summary": None,
                        "title": None,
                        "description": None,
                        "hashtags": None,
                    }
                    launch_status = "partial"
                    job_status = "processing"
                    job_stage = "user_fine_tune"

            send_runpod_webhook(
                job_id,
                {
                    "status": "processing",
                    "stage": "generating_metadata",
                    "duration": benchmark_results["Generating metadata"]
                },
                None,
                launch={
                    "transcript": transcript_data.get("text"),
                    "summary": result.get("summary"),
                    "title": result.get("title"),
                    "hashtags": result.get("hashtags"),
                    "description": result.get("description")

                }
            )

        send_runpod_webhook(
            job_id,
            {
                "status": job_status,
                "stage": job_stage,
                "duration": benchmark_results["🚀 Video processing pipeline"],
            },
            None,
            launch={
                "status": launch_status,
            }
        )

        if is_dev:
            save_transcript(transcript_data, output_dir)
            save_metadata(result, output_dir)
            logger.info("🛠 Running in DEV mode — skipping cleanup and shutdown.")
            return

        # Clean-up
        clean_up(output_dir)
        clean_up("input")

        # Shut-down pod instance
        shutdown_pod()

    except Exception as e:
        logger.exception(str(e))
        send_runpod_webhook(
            job_id,
            {
                "status": "error",
                "stage": job_stage,
                "error": str(e),
                "duration": benchmark_results["🚀 Video processing pipeline"],
            }
        )
        shutdown_pod()
