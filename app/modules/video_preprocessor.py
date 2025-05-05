import os
import subprocess
from typing import Dict
from app.logger import logger

OUTPUT_DIR: str = "output"


class VideoPreprocessor:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.frames_dir = os.path.join(self.output_dir, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)

    def get_video_resolution(self, video_path: str) -> int:
        logger.info(f"🔍 Checking resolution for: {video_path}")
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        width = int(result.stdout.strip())
        logger.info(f"📏 Video width detected: {width}px")
        return width

    def downscale_if_needed(self, input_path: str, target_width: int = 1280) -> str:
        downscaled_path = os.path.join(self.output_dir, "downscaled.mp4")
        width = self.get_video_resolution(input_path)
        if width > target_width:
            logger.info(f"📉 Downscaling video from {width}px to {target_width}px")
            subprocess.run([
                "ffmpeg", "-y", "-i", input_path,
                "-vf", f"scale={target_width}:-1",
                "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
                downscaled_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return downscaled_path
        else:
            logger.info(f"✅ No downscaling needed (width {width}px <= {target_width}px)")
            return input_path  # Use original

    def extract_frames(self, video_path: str, fps: int = 1) -> str:
        logger.info(f"🖼 Extracting {fps} FPS frames from: {video_path}")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"fps={fps}",
            os.path.join(self.frames_dir, "frame_%04d.jpg")
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.frames_dir

    def extract_audio(self, video_path: str) -> str:
        audio_path = os.path.join(self.output_dir, "audio.wav")
        logger.info(f"🔊 Extracting audio track from: {video_path}")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
            audio_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_path

    def preprocess(self, video_path: str) -> Dict:
        processed_video = self.downscale_if_needed(video_path)
        frames_path = self.extract_frames(processed_video, fps=1)
        audio_path = self.extract_audio(processed_video)

        return {
            "processed_video": processed_video,
            "frames_dir": frames_path,
            "audio_path": audio_path
        }
