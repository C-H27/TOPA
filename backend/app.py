from pathlib import Path
from time import monotonic

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .status_logic import TableState

app = FastAPI(title="Smart Table Finder")
tables: dict[int, TableState] = {}
frontend = Path(__file__).resolve().parents[1] / "frontend"


class Counts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    table_id: int = Field(gt=0)
    seats: int = Field(gt=0)
    people: int = Field(ge=0)
    items: int = Field(ge=0)


@app.post("/update")
async def update(counts: Counts):
    now = monotonic()
    table = tables.setdefault(counts.table_id, TableState())
    table.observe(counts.seats, counts.people, counts.items, now)
    return table.snapshot(counts.table_id, now)


@app.get("/status")
async def status():
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
