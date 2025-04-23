from typing import Dict
from app.logger import logger

class TranscriptScorer:
    def __init__(self, transcript_data: Dict, video_duration_sec: float):
        self.transcript = transcript_data
        self.video_duration = video_duration_sec

    def score(self) -> float:
        segments = self.transcript.get("segments", [])
        total_words = sum(len(s["text"].split()) for s in segments)
        total_time = self.video_duration / 60  # in minutes

        # Words per minute
        wpm = total_words / total_time if total_time > 0 else 0

        # Count hype/emotional words
        hype_words = {"insane", "omg", "crazy", "wtf", "bro", "cheater", "legit", "clutch", "fucking", "laugh", "go", "run", "sick", "god"}
        hype_count = sum(
            sum(1 for word in s["text"].lower().split() if word in hype_words)
            for s in segments
        )

        # Long gaps (e.g., 30s+ of no speech)
        long_gaps = 0
        for i in range(1, len(segments)):
            gap = segments[i]["start"] - segments[i-1]["end"]
            if gap > 30:
                long_gaps += 1

        # Compute basic score
        score = 0
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

        logger.info(f"📊 Transcript scoring: WPM={wpm:.1f}, Hype={hype_count}, Long Gaps={long_gaps}, Score={score:.2f}")
        return round(score, 2)
