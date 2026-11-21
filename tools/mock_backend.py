"""
Test server for the dashboard (no real backend or detector needed).
Uses only standard Python (nothing to install).

Run from the folder that contains frontend/:
    python3 mock_backend.py
Then open http://localhost:8000 (live) or http://localhost:8000/admin.html (admin).

Table IDs match the detector (studyspot-agent/main.py):
    1-3   group rooms (5, 5, 3 seats)
    4-7   study tables T1-T4 (6 seats)
    8-15  study tables T5-T12 (4 seats)
    16-21 wall desks D1-D6 (1 seat)
"""
import json
import os
import random
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(HERE, "frontend")
if not os.path.isdir(FRONTEND):                       # when this file is in tools/
    FRONTEND = os.path.join(os.path.dirname(HERE), "frontend")
PORT = 8000

SEATS = {1: 5, 2: 5, 3: 3,
         **{i: 6 for i in range(4, 8)},
         **{i: 4 for i in range(8, 16)},
         **{i: 1 for i in range(16, 22)}}

tables = [{"table_id": i, "seats": s, "people": random.randint(0, s),
           "items": random.randint(0, 2), "items_seconds": 0}
          for i, s in SEATS.items()]
people_so_far = 41


def status_of(t):
    if t["people"] >= t["seats"]:
        return "full"
    if t["people"] > 0:
        return "partly"
    return "items" if t["items"] else "free"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # always serve the newest page
        super().end_headers()

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global people_so_far
        if self.path.startswith("/status"):
            t = random.choice(tables)
            before = t["people"]
            t["people"] = random.randint(0, t["seats"])
            t["items"] = random.randint(0, 2)
            people_so_far += max(t["people"] - before, 0)
            for x in tables:
                x["items_seconds"] = x["items_seconds"] + 2 if status_of(x) == "items" else 0
            rows = [{"table_id": x["table_id"], "seats": x["seats"], "people": x["people"],
                     "status": status_of(x), "items_seconds": x["items_seconds"]} for x in tables]
            if "include_room=true" in self.path:
                self.send_json({"people_in_frame": None, "people_so_far": people_so_far, "tables": rows})
            else:
                self.send_json(rows)
        else:
            super().do_GET()

    def do_POST(self):
        # Fake video analysis for the admin page: made-up results every 10 s for 60 s
        if self.path.startswith("/upload"):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            rows = []
            for sec in range(0, 60, 10):
                for tid, seats in SEATS.items():
                    people = random.randint(0, seats)
                    items = 1 if people else random.randint(0, 1)
                    row = {"table_id": tid, "seats": seats, "people": people, "items": items}
                    rows.append({"video_seconds": float(sec), **row, "status": status_of(row)})
            self.send_json({"method": "mock", "room": [], "tables": rows,
                            "people_in_frame": None, "people_so_far": None})
        else:
            self.send_json({"detail": "Not found"}, 404)

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    print(f"Test server running: http://localhost:{PORT}  (Ctrl+C to stop)")
    print(f"Admin page:          http://localhost:{PORT}/admin.html")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
