import whisper
import torch
from app.logger import logger
from typing import Dict


class TranscriptGenerator:
    def __init__(self, model_name: str = "medium"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔌 Torch device selected: {self.device.upper()}")

        model_url = whisper._MODELS[model_name]
        model_path = whisper._download(model_url)

        logger.info(f"🔊 Loading Whisper model: {model_name}")
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model = whisper.Whisper(**checkpoint["model_kwargs"])
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        logger.info("✅ Whisper model loaded.")

    def transcribe(self, file_path: str) -> Dict:
        logger.info(f"🎧 Transcribing file: {file_path}")

        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.device)

        _, probs = self.model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        logger.info(f"🌐 Detected language: {detected_lang}")

        options = whisper.DecodingOptions()
        result = whisper.decode(self.model, mel, options)

        return {"text": result.text}
