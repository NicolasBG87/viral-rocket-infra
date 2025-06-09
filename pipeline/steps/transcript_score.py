from pipeline import JobContext, step
from util import logger


@step("transcript_score")
def run(ctx: JobContext):
    video_metadata = ctx.output.get("video_metadata")
    transcript = video_metadata.get("transcript")

    if not transcript or "segments" not in transcript:
        video_metadata["transcript_score"] = 0
        return

    segments = transcript["segments"]
    duration = video_metadata.get("duration", 0)

    total_words = sum(len(s["text"].split()) for s in segments)
    total_time_min = duration / 60 if duration > 0 else 1
    wpm = total_words / total_time_min

    hype_words = {"insane", "omg", "crazy", "wtf", "bro", "cheater", "legit", "clutch", "fucking",
                  "laugh", "go", "run", "sick", "god"}
    hype_count = sum(
        sum(1 for word in s["text"].lower().split() if word in hype_words)
        for s in segments
    )

    long_gaps = 0
    for i in range(1, len(segments)):
        if segments[i]["start"] - segments[i - 1]["end"] > 30:
            long_gaps += 1

    score = 0.0
    if wpm > 40:
        score += 0.4
    elif wpm > 20:
        score += 0.2

    if hype_count > 10:
        score += 0.3
    elif hype_count > 5:
        score += 0.2

    if long_gaps == 0:
        score += 0.3
    elif long_gaps < 3:
        score += 0.1

    logger.info(f"📊 Transcript score: {score:.2f} (WPM={wpm:.1f}, Hype={hype_count}, Gaps={long_gaps})")

    video_metadata["transcript_score"] = round(score, 2)
