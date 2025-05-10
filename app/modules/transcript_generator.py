from faster_whisper import WhisperModel
from typing import Dict
from app.logger import logger

MODEL_SIZE: str = "medium"
DEVICE: str = "cuda"


class TranscriptGenerator:
    def __init__(self):
        compute_type = "float16" if DEVICE == "cuda" else "int8"
        self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=compute_type)

    def transcribe(self, file_path: str) -> Dict:
        try:
            logger.info(f"🎧 Transcribing file: {file_path}")
            segments, info = self.model.transcribe(file_path, beam_size=5)

            transcript_segments = []
            full_text = []

            for seg in segments:
                transcript_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })
                full_text.append(seg.text.strip())

            return {
                "text": " ".join(full_text),
                "segments": transcript_segments,
                "language": info.language
            }
        except Exception as e:
            raise RuntimeError(f"Error: {e}")
