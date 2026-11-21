"""
Mock backend for testing the dashboard before the real backend is ready.
Uses only standard Python (nothing to install).

Run from the repository root:
    python3 tools/mock_backend.py
Then open http://localhost:8000

Tables (same IDs the detector must send):
    1-12  study tables, 6 seats
    13-15 group room tables
    16-23 wall desks, 1 seat
"""
import json
import os
import random
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
PORT = 8000

SEATS = {**{i: 6 for i in range(1, 13)},
         13: 5, 14: 5, 15: 5,
         **{i: 1 for i in range(16, 24)}}

tables = [{"table_id": i, "seats": s, "people": random.randint(0, s),
           "items": random.randint(0, 2), "items_seconds": 0}
          for i, s in SEATS.items()]
people_so_far = 41


def status_of(t):
    if t["people"] == 0 and t["items"] == 0:
        return "free"
    if t["people"] == 0:
        return "items"
    if t["people"] >= t["seats"]:
        return "full"
    return "partly"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # always serve the newest page
        super().end_headers()

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
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
            self.send_json([
                {"table_id": x["table_id"], "seats": x["seats"], "people": x["people"],
                 "status": status_of(x), "items_seconds": x["items_seconds"]}
                for x in tables
            ])
        elif self.path.startswith("/stats"):
            self.send_json({"people_so_far": people_so_far})
        else:
            super().do_GET()

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    print(f"Mock backend running: http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
