"""Run the fixed-camera detector on an uploaded demo clip."""
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter()
MAX_VIDEO_BYTES = 100 * 1024 * 1024
default_detector = Path(__file__).resolve().parents[1] / "studyspot-agent" / "main.py"


def csv_numbers(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        return [
            {key: value if key == "status" else float(value) if key == "video_seconds" else int(value)
             for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]


@router.post("/upload")
def upload_video(file: UploadFile):
    if Path(file.filename or "").suffix.lower() != ".mp4":
        raise HTTPException(415, "Upload an MP4 from the calibrated demo camera.")
    if not file.size:
        raise HTTPException(422, "The video is empty.")
    if file.size > MAX_VIDEO_BYTES:
        raise HTTPException(413, "The video exceeds 100 MiB.")
    detector = Path(os.getenv("TOPA_DETECTOR_SCRIPT", str(default_detector))).resolve()
    if not detector.is_file():
        raise HTTPException(503, "The studyspot-agent detector is missing on this server.")
    python = os.getenv("TOPA_DETECTOR_PYTHON", sys.executable)
    with TemporaryDirectory(prefix="topa-video-") as work:
        video = Path(work) / "input.mp4"
        output = Path(work) / "output"
        with video.open("wb") as target:
            shutil.copyfileobj(file.file, target)
        try:
            run = subprocess.run(
                [python, str(detector), "--video", str(video), "--output", str(output)],
                capture_output=True, text=True, timeout=40,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Analysis timed out. Try a shorter clip.") from None
        except OSError:
            raise HTTPException(503, "Could not start the configured detector.") from None
        if run.returncode:
            if "ModuleNotFoundError" in run.stderr or "ImportError" in run.stderr:
                raise HTTPException(503, "Install the detector's Python dependencies.")
            raise HTTPException(422, "The detector could not analyse this video.")
        return {
            "method": "fixed_camera_opencv",
            "room": csv_numbers(output / "room.csv"),
            "tables": csv_numbers(output / "tables.csv"),
            "people_in_frame": None,
            "people_so_far": None,
        }
