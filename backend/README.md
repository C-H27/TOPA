# Table status API

From the repository root, run with Python 3.10 or later:

```sh
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --port 8000
```

Use one worker. The server keeps current observations in memory and starts empty on restart. For a same-Wi-Fi demo, add `--host 0.0.0.0` and open the laptop's LAN address. Use a trusted demo network; the update endpoint accepts unauthenticated writes.

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
{"tables":[{"table_id":1,"seats":4,"people":0,"items":1,"status":"items_only","items_seconds":2}]}
```

The latest counts are instantaneous. The status is confirmed by matching observations at least **2 seconds** apart. A changed candidate restarts confirmation for that table. People at or above capacity are `full`; positive counts below capacity are `partly_taken`. With zero people, belongings give `items_only` and an empty table gives `free`. The belongings timer starts at the first observation in the confirmed interval and resets when a different status is confirmed.

Use `unknown` during startup or after 12 seconds without observations. On timeout, counts become null and the timer becomes zero. The next update starts a new confirmation interval. Table IDs and capacities are positive integers; counts are non-negative integers.

Place the student page at `frontend/index.html`. The API serves it at `/` and serves assets from the same directory. Restart after adding the frontend directory. Until the page is present, the root links to the status feed and interactive API docs.
