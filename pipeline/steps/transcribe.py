from faster_whisper import WhisperModel
from pipeline import JobContext, step
from util import logger


@step("transcribe")
def run(ctx: JobContext):
    video_metadata = ctx.output.get("video_metadata")
    transcript = video_metadata.get("transcript")
    path = video_metadata.get("path")

    if transcript:
        logger.info("🧠 Using YouTube transcript. Skipping Whisper.")
        return

    if not path:
        raise RuntimeError("No video path found in context.")

    logger.info("🎙️ Starting Whisper transcription...")

    model_size = "medium"
    device = "cuda"
    compute_type = "float16" if device == "cuda" else "int8"

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    segments_gen, info = model.transcribe(path, beam_size=5)
    segments = list(segments_gen)

    transcript_segments = []
    full_text = []

    for seg in segments:
        text = seg.text.strip()
        if text:
            transcript_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": text
            })
            full_text.append(text)

    video_metadata["transcript"] = {
        "text": " ".join(full_text),
        "segments": transcript_segments,
        "duration": segments[-1].end if transcript_segments else 0,
        "source": "Whisper"
    }

    logger.info(f"📝 Whisper transcript complete. Language: {info.language}")
