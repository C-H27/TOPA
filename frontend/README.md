# Dashboard (frontend)

Two pages, no build step and no internet dependency:

| File | Page | For |
| --- | --- | --- |
| `index.html` | Live dashboard at `/` | Students: which tables are free right now |
| `admin.html` | Admin at `/admin.html` | Staff: upload a camera video and see the table results over time |
| `layout.js` | – | The room layout and table IDs, shared by both pages |
| `style.css` | – | Shared look for both pages |

The two pages link to each other with the **Live** / **Admin** buttons in the header.

## Room layout and table IDs

The layout matches the Learning Center camera view, and the IDs match the detector (`studyspot-agent/main.py`, `layout()`):

| table_id | Shown as | Area |
| --- | --- | --- |
| 1–3 | G1–G3 | Group Room 1–3 (top) |
| 4–15 | T1–T12 | Study tables, 4 x 3 grid, left to right, top to bottom |
| 16–23 | D1–D8 | Wall desks on the right, top to bottom |

The detector currently watches desks 16–21. Any desk that never appears in the data is hidden automatically. Seat counts on the cards come from the data. To change IDs or the layout, edit `layout.js` only.

Statuses: `free` = Empty (green), `partly` = Semi-occupied (yellow), `full` = Occupied (red), `items` = Items only (grey), table missing = No data (light grey).

## Live dashboard (`index.html`)

- Reads `GET /status?include_room=true` every 2 seconds. Works with either reply: a list of tables, or `{"tables": [...], "people_so_far": N}`.
- Summary: empty, semi-occupied, occupied, items only, people now, people so far today (shows "–" until the backend sends `people_so_far`).

## Admin page (`admin.html`)

1. **Choose video** (MP4, up to 100 MB) and press **Analyse video**.
2. The page sends it to `POST /upload` (backend `video_upload.py`), which runs the detector on the clip.
3. Results: the video plays on the left; the room layout below shows each table's status at that moment. The slider and the timeline table jump to any analysed moment (the detector samples every 10 seconds).

If the server uses a write token (`TOPA_WRITE_TOKEN`), enter it in the token box. Errors (wrong file type, too big, detector missing, timeout) are shown in plain words.

## Testing without the real backend

- **Quickest:** double-click `index.html` or `admin.html`. Both run with made-up data.
- **Test server** (fake live data and a fake `/upload`):

  ```
  python3 tools/mock_backend.py
  ```

  Open `http://localhost:8000` and `http://localhost:8000/admin.html`. Stop it with Ctrl+C before starting the real backend, because both use port 8000.
