"""Measure occupancy in a fixed-camera learning centre demo."""
import argparse
import csv
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

import cv2
import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
# Settings for the team demo
DEFAULT_VIDEO = ROOT / "videos" / "learning_center_1st_floor_3min_1080p.mp4"
DEFAULT_OUTPUT = ROOT / "output"
SUMMARY_SECONDS = 10
PUBLISH_SECONDS = 2.5
SIZE = (960, 540)


def layout():
    """Chair centres and tabletop centres in the resized reference image."""
    tables = [
        ([(132, 80), (268, 80), (169, 109), (200, 109), (231, 109)], (150, 62, 250, 99)),
        ([(432, 80), (568, 80), (469, 109), (500, 109), (531, 109)], (450, 62, 550, 99)),
        ([(668, 159), (703, 159), (738, 159)], (650, 128, 755, 148)),
    ]
    for x in (180, 340, 500, 660):
        chairs = [(x + dx, y) for y in (217, 274) for dx in (-31, 0, 31)]
        tables.append((chairs, (x-50, 227, x+50, 263)))
    for y in (350, 455):
        for x in (180, 340, 500, 660):
            chairs = [(x + dx, y + dy) for dy in (-28, 29) for dx in (-19, 19)]
            tables.append((chairs, (x-37, y-17, x+37, y+17)))
    for y in (230, 280, 330, 380, 430, 480):
        tables.append(([(855, y)], (874, y-16, 909, y+16)))
    return tables


def observe(frame, reference, tables):
    current = cv2.resize(frame, SIZE, interpolation=cv2.INTER_AREA)
    delta = cv2.absdiff(current, reference)
    changed = np.max(delta, axis=2) >= 37
    rows = []
    for table_id, (chairs, box) in enumerate(tables, start=1):
        people = sum(bool(changed[y-7:y+8, x-7:x+8].mean() >= 0.19) for x, y in chairs)
        x1, y1, x2, y2 = box
        # A tabletop change indicates object presence, rather than an object count.
        surface = changed[y1+3:y2-3, x1+3:x2-3]
        items = int(surface.sum() >= 26 and surface.mean() >= 0.018)
        rows.append({"table_id": table_id, "seats": len(chairs), "people": people, "items": items})
    return rows


def status(row):
    if row["people"] >= row["seats"]:
        return "full"
    if row["people"]:
        return "partly"
    return "items" if row["items"] else "free"


def publish(url, rows):
    headers = {"Content-Type": "application/json"}
    token = os.getenv("TOPA_WRITE_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=json.dumps({"tables": rows}).encode(), headers=headers, method="POST")
    with urlopen(req, timeout=4) as response:
        response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, default=DEFAULT_VIDEO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--backend", help="FastAPI origin, e.g. http://127.0.0.1:8000")
    args = parser.parse_args()
    cap = cv2.VideoCapture(str(args.video))
    ok, first = cap.read()
    if not ok:
        cap.release()
        raise SystemExit(f"Cannot read {args.video}")
    reference = cv2.resize(first, SIZE, interpolation=cv2.INTER_AREA)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps <= 0 or frame_count <= 0:
        cap.release()
        raise SystemExit("The video must provide a frame rate and duration.")

    tables = layout()
    args.output.mkdir(parents=True, exist_ok=True)
    interval = PUBLISH_SECONDS if args.backend else SUMMARY_SECONDS
    api = args.backend.rstrip("/") + "/update/batch" if args.backend else None
    successful_updates = 0
    clock_start = time.monotonic()
    try:
        with (args.output/"tables_status.csv").open("w", encoding="utf-8", newline="") as detail, (
            args.output/"occupancy_log.csv"
        ).open("w", encoding="utf-8", newline="") as summary:
            table_fields = ("video_seconds", "table_id", "seats", "people", "items", "status")
            room_fields = ("video_seconds", "people_seated", "free", "partly", "full", "items")
            writer = csv.DictWriter(detail, fieldnames=table_fields)
            totals_writer = csv.DictWriter(summary, fieldnames=room_fields)
            writer.writeheader()
            totals_writer.writeheader()
            for step in range(int(np.ceil(frame_count/fps/interval))):
                instant = step * interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, round(instant*fps))
                ok, frame = cap.read()
                if not ok:
                    raise SystemExit(f"Cannot decode the frame at {instant:g}s.")
                rows = observe(frame, reference, tables)
                if api:
                    time.sleep(max(0, clock_start + instant - time.monotonic()))
                classified = [{**row, "status": status(row)} for row in rows]
                writer.writerows({"video_seconds": instant, **row} for row in classified)
                totals = {name: 0 for name in ("free", "partly", "full", "items")}
                for row in classified:
                    totals[row["status"]] += 1
                snapshot = {"video_seconds": instant, "people_seated": sum(r["people"] for r in rows), **totals}
                if instant % SUMMARY_SECONDS == 0:
                    totals_writer.writerow(snapshot)
                    print(snapshot, flush=True)
                detail.flush()
                summary.flush()
                live = {**snapshot, "people_in_frame": None, "people_so_far": None, "tables": classified}
                temporary = args.output / "live.json.tmp"
                temporary.write_text(json.dumps(live), encoding="utf-8")
                temporary.replace(args.output / "live.json")
                if api:
                    try:
                        publish(api, rows)
                        successful_updates += 1
                    except OSError as exc:
                        print(f"Backend update failed at {instant:g}s: {exc}", flush=True)
    finally:
        cap.release()
    print(f"CSV output: {args.output}")
    if api and not successful_updates:
        raise SystemExit("No backend updates succeeded.")


if __name__ == "__main__":
    main()
