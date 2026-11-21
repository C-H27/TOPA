# Dashboard (frontend)

`index.html` is the live dashboard students open in the browser. It is a single file with no build step and no internet dependency.

## What it shows

- **Summary:** empty tables, semi-occupied, occupied, items only, people now, people so far today
- **Room layout** matching the Learning Center camera view:
  - Group Room 1–3 at the top (G1–G3)
  - Study tables T1–T12 in a 4 x 3 grid, numbered left to right, top to bottom
  - Wall desks D1–D8 on the right, top to bottom
- **Each table card:** name, one dot per seat (filled = someone sitting), people / seats, status, and a timer for items-only tables
- **Phones:** the sections stack vertically

Status colours:

| Status from `/status` | Shown as | Colour |
| --- | --- | --- |
| `free` | Empty | Green |
| `partly` | Semi-occupied | Yellow |
| `full` | Occupied | Red |
| `items` | Items only (nobody there) | Grey |
| table missing from `/status` | No data | Light grey |

## Table IDs (the detector must send these `table_id` values)

| table_id | Shown as | Area |
| --- | --- | --- |
| 1–12 | T1–T12 | Study tables (6 seats) |
| 13–15 | G1–G3 | Group Room 1–3 |
| 16–23 | D1–D8 | Wall desks (1 seat) |

The seat count shown comes from the backend, so it always matches what the detector sends.

## Data it reads

- `GET /status` every 2 seconds, for example
  `[{"table_id": 1, "seats": 6, "people": 2, "status": "partly", "items_seconds": 0}]`
- `GET /stats` (optional) `{"people_so_far": 42}` for "People so far today". Shows "–" until the backend provides it.

The backend (`backend/app.py`) serves this folder at `http://localhost:8000/`. Restart the backend after adding or changing the `frontend/` folder.

## Testing without the backend

- **Quickest:** double-click `index.html`. It runs with fake data.
- **With a test server** that sends fake data in the real `/status` format for all 23 tables:

  ```
  python3 tools/mock_backend.py
  ```

  Then open `http://localhost:8000`. Stop it with Ctrl+C before starting the real backend, because both use port 8000.

## Changing the layout

The tables are defined near the top of the script in `index.html` (`GROUP_ROOMS`, `STUDY_TABLES`, `WALL_DESKS`). For a room with a different layout, change those lists and the IDs to match the detector's table zones.
