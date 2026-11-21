import os
from pathlib import Path
from secrets import compare_digest
from time import monotonic

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .status_logic import Status, TableState

app = FastAPI(title="Smart Table Finder")
tables: dict[int, TableState] = {}
frontend = Path(__file__).resolve().parents[1] / "frontend"
bearer = HTTPBearer(auto_error=False)
write_token = os.getenv("TOPA_WRITE_TOKEN")


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


def authorize_update(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if write_token and (
        credentials is None
        or not compare_digest(credentials.credentials.encode(), write_token.encode())
    ):
        raise HTTPException(401, "Valid write token required.", headers={"WWW-Authenticate": "Bearer"})


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


@app.get("/status", response_model=TableReadings)
async def status(response: Response):
    response.headers["Cache-Control"] = "no-store"
    now = monotonic()
    return {"tables": [tables[key].snapshot(key, now) for key in sorted(tables)]}


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
