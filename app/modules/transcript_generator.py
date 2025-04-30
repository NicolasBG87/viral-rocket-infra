import whisper
import torch
from app.logger import logger
from typing import Dict


class TranscriptGenerator:
    def __init__(self, model_name: str = "medium"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔌 Torch device selected: {self.device.upper()}")

        logger.info(f"🔊 Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name, device=self.device)
        logger.info("✅ Whisper model loaded.")

    def transcribe(self, file_path: str) -> Dict:
        logger.info(f"🎧 Transcribing file: {file_path}")
        result = self.model.transcribe(file_path)
        return {
            "text": result["text"],
            "segments": result.get("segments"),
            "language": result.get("language")
        }
