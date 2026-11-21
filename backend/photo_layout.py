"""Forward a selected image to the team's hosted table-occupancy workflow."""
import base64
import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field, ValidationError

router = APIRouter()
config_file = Path(__file__).resolve().parents[1] / "studyspot-agent" / ".env"


class Box(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    label: str = Field(alias="class", min_length=1)


class Dimensions(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class DetectionFrame(BaseModel):
    image: Dimensions
    predictions: list[Box]


def run_workflow(image, settings):
    key = settings.get("ROBOFLOW_API_KEY")
    if not key:
        raise HTTPException(503, "Set ROBOFLOW_API_KEY on the backend to enable photo detection.")
    workspace = settings.get("ROBOFLOW_WORKSPACE") or "husnis-workspace-ajtaz"
    workflow = settings.get("ROBOFLOW_WORKFLOW") or "table-occupancy-prototype-1795260896010"
    endpoint = f"https://serverless.roboflow.com/{quote(workspace, safe='')}/workflows/{quote(workflow, safe='')}"
    payload = {"inputs": {"image": {"type": "base64", "value": base64.b64encode(image).decode("ascii")}}}
    request = Request(endpoint, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}",
    })
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(502, "Roboflow request failed. Check the workflow, credentials and quota.") from exc


@router.post("/detect/photo")
def photo_layout(file: UploadFile):
    image = file.file.read(8 * 1024 * 1024 + 1)
    if len(image) > 8 * 1024 * 1024:
        raise HTTPException(413, "Choose an image under 8 MiB.")
    if not image.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")):
        raise HTTPException(415, "Choose a JPEG or PNG image.")
    settings = {**dotenv_values(config_file), **os.environ}
    result = run_workflow(image, settings)
    output_name = settings.get("ROBOFLOW_OUTPUT") or "predictions"
    try:
        frame = DetectionFrame.model_validate(result["outputs"][0][output_name])
    except (ValidationError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(502, f"Expected table boxes and image dimensions in workflow output '{output_name}'.") from exc
    return frame.model_dump()
