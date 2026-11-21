import os
from pathlib import Path
from secrets import compare_digest
from time import monotonic
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .status_logic import Status, TableState
from .video_upload import router as upload_router
from .photo_layout import router as photo_router

app = FastAPI(title="Smart Table Finder")
tables: dict[int, TableState] = {}
frontend = Path(__file__).resolve().parents[1] / "frontend"
bearer = HTTPBearer(auto_error=False)
write_token = os.getenv("TOPA_WRITE_TOKEN")
room_reading = None
ROOM_STALE_SECONDS = 30


class Counts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    table_id: int = Field(gt=0)
    seats: int = Field(gt=0)
    people: int = Field(ge=0)
    items: int = Field(ge=0)


class CountsBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tables: list[Counts] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check_unique_tables(self):
        if len({table.table_id for table in self.tables}) != len(self.tables):
            raise ValueError("Each table ID may appear only once per batch.")
        return self


class RoomCounts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    people_in_frame: int | None = Field(default=None, ge=0)
    people_so_far: int | None = Field(default=None, ge=0)


class TableReading(BaseModel):
    table_id: int
    seats: int
    people: int | None
    items: int | None
    status: Status
    items_seconds: int
    pending_status: Status | None


class TableReadings(BaseModel):
    tables: list[TableReading]


class DashboardTable(BaseModel):
    table_id: int
    seats: int
    people: int
    status: Literal["free", "partly", "full", "items"]
    items_seconds: int


class DashboardStatus(RoomCounts):
    tables: list[DashboardTable]


def authorize_update(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if write_token and (
        credentials is None
        or not compare_digest(credentials.credentials.encode(), write_token.encode())
    ):
        raise HTTPException(401, "Valid write token required.", headers={"WWW-Authenticate": "Bearer"})


app.include_router(upload_router, dependencies=[Depends(authorize_update)])
app.include_router(photo_router)


@app.post("/update/room", response_model=RoomCounts, dependencies=[Depends(authorize_update)])
async def update_room(counts: RoomCounts):
    global room_reading
    room_reading = (monotonic(), counts)
    return counts


def current_room() -> RoomCounts:
    if room_reading is not None:
        observed_at, counts = room_reading
        if monotonic() - observed_at < ROOM_STALE_SECONDS:
            return counts
    return RoomCounts()


def record(counts: Counts, now: float) -> dict:
    table = tables.setdefault(counts.table_id, TableState())
    table.observe(counts.seats, counts.people, counts.items, now)
    return table.snapshot(counts.table_id, now)


@app.post("/update", response_model=TableReading, dependencies=[Depends(authorize_update)])
async def update(counts: Counts):
    return record(counts, monotonic())


@app.post("/update/batch", response_model=TableReadings, dependencies=[Depends(authorize_update)])
async def update_batch(batch: CountsBatch):
    now = monotonic()
    return {"tables": [record(counts, now) for counts in batch.tables]}


def current_readings():
    now = monotonic()
    return [tables[key].snapshot(key, now) for key in sorted(tables)]


@app.get("/status", response_model=list[DashboardTable] | DashboardStatus)
async def status(response: Response, include_room: bool = False):
    response.headers["Cache-Control"] = "no-store"
    aliases = {"free": "free", "partly_taken": "partly", "full": "full", "items_only": "items"}
    rows = [
        {**row, "status": aliases[row["status"]]}
        for row in current_readings()
        if row["status"] in aliases
    ]


    if include_room:
        return {"tables": rows, **current_room().model_dump()}
    return rows


@app.get("/api/status", response_model=TableReadings)
async def detailed_status(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"tables": current_readings()}


@app.get("/", include_in_schema=False)
async def dashboard():
    index = frontend / "index.html"
    if index.is_file():
        return FileResponse(index)
    return HTMLResponse("""<!doctype html><html lang="en"><title>Smart Table Finder</title>
        <h1>Smart Table Finder backend</h1><p>The API is ready.
        <a href="/status">View table statuses</a> or <a href="/docs">test the API</a>.</p></html>""")


if frontend.is_dir():
    app.mount("/", StaticFiles(directory=frontend), name="frontend")
