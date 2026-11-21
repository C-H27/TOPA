#!/bin/bash
# Smart Table Finder - one-command start on macOS / Linux.
# Usage: ./run-mac.sh            (backend + detector on the demo video)
#        ./run-mac.sh --lan      (also reachable from phones on the same Wi-Fi)
#        ./run-mac.sh --no-detector
cd "$(dirname "$0")" || exit 1
HOST=127.0.0.1; DETECT=1
for a in "$@"; do
  case "$a" in --lan) HOST=0.0.0.0 ;; --no-detector) DETECT=0 ;; esac
done
PORT=${TOPA_PORT:-8000}
VIDEO=${TOPA_VIDEO:-studyspot-agent/videos/learning_center_2.mp4}

if [ ! -x .venv-mac/bin/python ]; then
  echo "Creating Python environment (first run only)..."
  python3 -m venv .venv-mac || exit 1
fi
.venv-mac/bin/python -m pip install -q --disable-pip-version-check \
  -r backend/requirements.txt -r studyspot-agent/requirements.txt || exit 1

if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT is busy (old server or mock_backend.py still running?). Stop it or run: TOPA_PORT=8001 ./run-mac.sh"
  exit 1
fi

.venv-mac/bin/python -m uvicorn backend.app:app --host "$HOST" --port "$PORT" &
BACKEND=$!
trap 'kill $BACKEND 2>/dev/null' EXIT INT TERM
for i in $(seq 1 20); do curl -s "http://127.0.0.1:$PORT/status" >/dev/null && break; sleep 0.5; done

echo
echo "Dashboard: http://127.0.0.1:$PORT/"
echo "Admin:     http://127.0.0.1:$PORT/admin.html"
echo "Photo:     http://127.0.0.1:$PORT/photo.html  (needs ROBOFLOW_API_KEY in studyspot-agent/.env)"
if [ "$HOST" = 0.0.0.0 ]; then
  IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')
  echo "Phone:     http://$IP:$PORT/"
fi
echo "Press Ctrl+C to stop."
echo

if [ "$DETECT" = 1 ]; then
  if [ -f "$VIDEO" ]; then
    .venv-mac/bin/python studyspot-agent/main.py --video "$VIDEO" --backend "http://127.0.0.1:$PORT" --loop
  else
    echo "Demo video not found: $VIDEO"
    echo "Put learning_center_2.mp4 in studyspot-agent/videos/ for live counts. Backend keeps running."
    wait $BACKEND
  fi
else
  wait $BACKEND
fi
