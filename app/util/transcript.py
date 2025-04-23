import os
import json
from app.logger import logger

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
