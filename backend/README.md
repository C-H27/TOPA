# Table status API

From the repository root, run with Python 3.10 or later:

```sh
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --port 8000
```

Use one worker. The server keeps current observations in memory and starts empty on restart. For a same-Wi-Fi demo, add `--host 0.0.0.0` and open the laptop's LAN address. Set the write token described below to restrict updates on a shared network.

## Detection handoff

POST one JSON object per table every 2 to 3 seconds. Send zero counts for empty tables, including when nothing was detected. Example using curl in Bash:

```sh
curl -X POST http://localhost:8000/update -H 'Content-Type: application/json' -d '{"table_id":1,"seats":4,"people":0,"items":1}'
sleep 2
curl -X POST http://localhost:8000/update -H 'Content-Type: application/json' -d '{"table_id":1,"seats":4,"people":0,"items":1}'
curl http://localhost:8000/status
```

## Dashboard handoff

Poll `GET /status` every two seconds. It returns `{"tables":[]}` before the first update. After the example above:

```json
{"tables":[{"table_id":1,"seats":4,"people":0,"items":1,"status":"items_only","items_seconds":2,"pending_status":null}]}
```

The latest counts are instantaneous. The status is confirmed by matching observations at least **2 seconds** apart. A changed candidate restarts confirmation for that table. People at or above capacity are `full`; positive counts below capacity are `partly_taken`. With zero people, belongings give `items_only` and an empty table gives `free`. The belongings timer starts at the first observation in the confirmed interval and resets when a different status is confirmed.

Use `unknown` during startup or after 12 seconds without observations. On timeout, counts become null and the timer becomes zero. The next update starts a new confirmation interval. Table IDs and capacities are positive integers; counts are non-negative integers.

Place the student page at `frontend/index.html`. The API serves it at `/` and serves assets from the same directory. Restart after adding the frontend directory. Until the page is present, the root links to the status feed and interactive API docs.

## Batch updates and write access

A detector can also send one frame's results to `POST /update/batch` as
`{"tables":[{"table_id":1,"seats":4,"people":0,"items":1}]}`.
Submit 1 to 100 distinct table IDs per batch. An invalid row or duplicate ID rejects the entire batch.
Clients can continue sending individual tables to `POST /update`.

Set `TOPA_WRITE_TOKEN` before starting the server to require
`Authorization: Bearer <token>` on both write routes. The dashboard can still read `GET /status`
without a token. Keep the token in the detector's environment when using a shared network.

A gap longer than four seconds restarts a pending change. This gives the detector's normal
2- to 3-second updates some slack and prevents an old observation from confirming a change
after a brief disconnect. On a capacity change, the status returns to unknown while the server
confirms the new reading. The `pending_status` field is null when nothing is awaiting confirmation.
Use `status` for the table colour.

## One-laptop integration rehearsal

1. Start FastAPI on the demo laptop on port 8000. Bind it to
   `0.0.0.0` for phone access. The detector on that same laptop can
   publish to `http://127.0.0.1:8000/update`.
2. Agree on 3 or 4 table IDs and capacities with the detector and dashboard
   owners. Confirm that every monitored table gets a record on each
   detection cycle, including empty tables with both counts set to zero.
3. Open `/status` on the demo laptop and open the dashboard on a phone
   using the laptop's LAN address. Verify that the same table ID updates
   on both screens. Display `status` and use `items_seconds` for the timer.
4. Replay the video at normal playback speed. Pick a section where someone
   leaves an item and later collects it. Verify `partly_taken` to
   `items_only` to `free`. Each state needs at least two matching
   observations spaced at least two seconds apart. If the clip has no such
   section, verify the four states on separate video segments.
5. Stop the detector. Check that the last state becomes `unknown` after
   12 seconds, then restart it and confirm that updates return.

For the results section, record the clip timestamps, table IDs, expected
states, actual API states, and any misses. Label mock-count tests separately
from detection tests on the team's synthetic video. The API receives counts
and serves the floor plan. It does not receive video frames.
