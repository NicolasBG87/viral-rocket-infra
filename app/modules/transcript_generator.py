import os
import whisper
import torch
from app.logger import logger
import json
from typing import Dict


class TranscriptGenerator:
    def __init__(self, model_name: str = "medium"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔌 Torch device selected: {self.device.upper()}")

        logger.info(f"🔊 Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logger.info("✅ Whisper model loaded.")

    def transcribe(self, file_path: str, output_dir: str) -> Dict:
        logger.info(f"🎧 Transcribing file: {file_path}")

        result = self.model.transcribe(file_path)
        text = result['text']

        os.makedirs(output_dir, exist_ok=True)

        # Save plain text
        txt_path = os.path.join(output_dir, "transcript.txt")
        with open(txt_path, "w") as f:
            f.write(text)
        logger.info(f"📄 Transcript text saved to {txt_path}")

        # Save full JSON
        json_path = os.path.join(output_dir, "transcript.json")
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"🧠 Transcript data saved to {json_path}")

        return result
