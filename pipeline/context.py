from dataclasses import dataclass, field
from typing import Optional, List, Literal, TypedDict


class InputPayload(TypedDict):
    video_url: str
    game_title: str
    game_mode: Optional[str]
    tone: Literal["neutral", "sarcastic", "hyped", "analytical", "chill", "funny", "toxic"]
    duration_limit: str
    quality_limit: str
    mode: Literal["standard", "user_enhanced"]


class TranscriptSegment(TypedDict):
    start: float
    end: float
    text: str


class Transcript(TypedDict):
    text: str
    segments: List[TranscriptSegment]
    duration: float
    source: str


class Chapter(TypedDict):
    start_time: float
    end_time: float
    title: str


class VideoMetadata(TypedDict, total=False):
    title: Optional[str]
    thumbnail: Optional[str]
    description: Optional[str]
    transcript: Optional[Transcript]
    duration: Optional[str]
    height: Optional[int]
    width: Optional[int]
    resolution: Optional[str]
    tags: List[str]
    channel: Optional[str]
    chapters: Optional[List[Chapter]]
    view_count: Optional[int]
    original_url: Optional[str]
    path: Optional[str]


class OutputData(TypedDict, total=False):
    video_metadata: Optional[VideoMetadata]
    title: Optional[str]
    description: Optional[str]
    summary: Optional[str]
    chapters: Optional[List[Chapter]]


@dataclass
class JobContext:
    job_id: str
    is_dev: bool
    webhook_url: str

    input: InputPayload = field(default_factory=dict)
    output: OutputData = field(default_factory=dict)

    output_dir: str = "output"

    status: str = "queued"
    stage: str = "init"
    errors: List[str] = field(default_factory=list)
