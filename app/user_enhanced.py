import requests
import os
from urllib.parse import urljoin
from app.logger import logger
from app.util.cleanup import clean_up
from app.util.shutdown_pod import shutdown_pod
from app.util.timer import benchmark, benchmark_results
from app.util.save_output import save_metadata, save_transcript_text
from app.modules.metadata_generator import MetadataGenerator
from app.util.send_runpod_webhook import send_runpod_webhook


def user_enhanced(output_dir, job_id, game_title, is_dev):
    job_status = "processing"
    job_stage = "generating_metadata"

    try:
        with benchmark("🚀 User enhanced processing pipeline"):
            logger.info("👍 Generating user enhanced metadata.")
            with benchmark("Generating metadata"):
                if is_dev:
                    transcript = "for queer countrymen Gear up, we aren't going on a windy walk here Come on, come on, jump, jump! Throwing smoke! Counter-terrorists win! Nice! Deploying flashbang. Moving, moving! Laying down smoke! Extend your reaction! Fire! Fire! Fire! Fire! Fire! Fire! Fire! Extend your reaction! Flashbang! Grenade! Extend your reaction! Throwing flashbang. Throwing a grenade! Counter-terrorists win! Best of the best! Fire! Smoke! Deploying fire! Throwing smoke! Throwing flashbang. Grenade out! Throwing a grenade! It's injury! Smoke! Throwing a grenade! Smoke! Fire! Fire! Fire! Fire! Fire! Fire! Fire! Enemies changing positions! Fire! Enemies changing positions! Blackout! Whistling! Whistling! way to go boys remember, this is bandit country, shoot everything that moves and then the airy throwing fire laying down smoke so terrorists win Throwing grenade out. Throwing fire. It's Sanctuary out. Throwing flashbang. Throwing grenade. Throwing flashbang. Throwing grenade. Throwing flashbang. Throwing flashbang. Counter-terrorists win. I like this. Deploying flashbang. Move it, move it. Throwing fire. It's Sanctuary. Throwing a grenade. Flashbang. Smoke. Flashbang. Grenade out. Throwing fire. Grenade out. Grenade. Grenade out, smoke. Deploying flashbang. Grenade out. Grenade out. It's Sanctuary out. Stairs. Bumped out. Grenade out. Throwing grenade. Grenade out. Throwing a grenade. Grenade out. The bomb has been planted. The shooting is off. The bomb has been defused. Counter-terrorists win. There you go. Let's move out. It's an injury. Fire in the hole. Throwing a grenade. Throwing fire. The bomb has been planted. The bomb has been defused. Grenade out. The bomb has been defused. Counter-terrorists win. Right on. Remove any totes in your head. It's us or them. It's an injury. It's in the area. The grenade is out. Smoke. Throwing flashbangs. Counter-terrorists win. Counter-terrorists win. Throwing smoke. Lock and load. Throwing smoke. Throwing fire. Throwing flashbangs. Laying down smoke. Grenade. Throwing flashbangs. Deploying flashbangs. Grenade. Throwing fire. Throwing a grenade. Counter-terrorists win. Now we can stop right into them. Right into them. This is our fight. No more talking. Now we fight! Let's throw the grenade! Landed. Bomb has been planted. Terrorists win. I fear no man. I fear no man. Agreed. Come on! Let's go! Throwing smoke. Throwing a flashbang. Flashbang! Smoke! Bomb has been planted. Bomb has been defused. Counter-terrorists win. Bomb has been defused. Counter-terrorists win. Bomb has been defused. Counter-terrorists win. Move it! Move it! Let's throw the flashbang. Throwing flashbangs. Grenade. Throwing a grenade. Grenade. Throwing fire. Landed. Landed. Throwing fire. Flashbang. Terrorists win. It seems you can kill us. It's over. We are going to do this."
                    user_payload = {
                        "game_title": "Counter Strike 2",
                        "game_mode": "Competitive match on Train",
                        "video_type": "Gameplay (No Commentary)",
                        "tone": "toxic"
                    }
                else:
                    base_api_url = os.getenv("WEBHOOK_URL")
                    api_url = urljoin(base_api_url, "processing/runpod-get-payload")
                    response = requests.get(f"{api_url}?job_id={job_id}")
                    response.raise_for_status()
                    data = response.json()
                    transcript = data.get('transcript')
                    user_payload = data.get('userPayload')

                mg = MetadataGenerator()
                result = mg.generate_user_enhanced(game_title, transcript, user_payload)

            send_runpod_webhook(
                job_id,
                {
                    "status": job_status,
                    "stage": job_stage,
                    "duration": benchmark_results["Generating metadata"]
                },
                None,
                launch={
                    "transcript": transcript,
                    "summary": result.get("summary"),
                    "title": result.get("title"),
                    "hashtags": result.get("hashtags"),
                    "description": result.get("description")

                }
            )

        send_runpod_webhook(
            job_id,
            {
                "status": "completed",
                "stage": "done",
                "duration": benchmark_results["🚀 User enhanced processing pipeline"],
            },
            None,
            launch={
                "status": "complete",
            }
        )

        if is_dev:
            save_transcript_text(transcript, output_dir)
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
                "duration": benchmark_results["🚀 User enhanced processing pipeline"],
            }
        )
        shutdown_pod()
