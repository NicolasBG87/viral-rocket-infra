import os
import json
from app.logger import logger


def save_metadata(metadata: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # Save structured JSON
    json_path = os.path.join(output_dir, "metadata.json")
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"💾 Metadata JSON saved to {json_path}")

def save_transcript(transcript_data: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # Save full plain text
    text = transcript_data.get("text", "")
    with open(os.path.join(output_dir, "transcript.txt"), "w") as f:
        f.write(text)

    # Save full JSON
    with open(os.path.join(output_dir, "transcript.json"), "w") as f:
        json.dump(transcript_data, f, indent=2)

    logger.info(f"💾 Transcript saved to: {output_dir}/transcript.txt and transcript.json")

def save_transcript_text(transcript: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # Save full plain text
    with open(os.path.join(output_dir, "transcript.txt"), "w") as f:
        f.write(transcript)

    logger.info(f"💾 Transcript saved to: {output_dir}/transcript.txt")