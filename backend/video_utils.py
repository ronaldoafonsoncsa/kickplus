import subprocess
import os
import base64
from pathlib import Path
from typing import Optional


def extract_frames(video_path: str, num_frames: int = 4) -> list[str]:
    """Extract evenly spaced frames from a video and return as base64 strings."""
    video_path = Path(video_path)
    frames_dir = video_path.parent / f"{video_path.stem}_frames"
    frames_dir.mkdir(exist_ok=True)

    duration = _get_video_duration(str(video_path))
    if duration is None or duration <= 0:
        raise ValueError("Could not determine video duration.")

    interval = duration / (num_frames + 1)
    frame_paths = []

    for i in range(1, num_frames + 1):
        timestamp = interval * i
        output_path = frames_dir / f"frame_{i:02d}.jpg"
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-vf", "scale=480:-1",
                "-q:v", "5",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if output_path.exists():
            frame_paths.append(str(output_path))

    if not frame_paths:
        raise ValueError("No frames could be extracted from the video.")

    frames_b64 = []
    for path in frame_paths:
        with open(path, "rb") as f:
            frames_b64.append(base64.b64encode(f.read()).decode("utf-8"))

    # Cleanup
    for path in frame_paths:
        os.remove(path)
    frames_dir.rmdir()

    return frames_b64


def _get_video_duration(video_path: str) -> Optional[float]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return None
