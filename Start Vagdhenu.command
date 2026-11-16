#!/bin/bash
# Double-click in Finder to start the Vāgdhenu chant studio and open it in your browser.
# The studio keeps running after you close this window; "Stop Vagdhenu.command" stops it.
cd "$(dirname "$0")" || exit 1

PORT="${VAGDHENU_PORT:-7860}"
# 127.0.0.1 = this Mac only; 0.0.0.0 = also phones/tablets on the same Wi-Fi
# ("Start Vagdhenu for Phone.command" sets this).
HOST="${VAGDHENU_HOST:-127.0.0.1}"
URL="http://localhost:$PORT"
LOG_DIR="out/logs"
LOG="$LOG_DIR/server.log"
PID_FILE="$LOG_DIR/server.pid"
mkdir -p "$LOG_DIR"

if curl -s -o /dev/null --max-time 2 "$URL"; then
  echo "Vāgdhenu is already running → $URL"
  [ -z "$VAGDHENU_NO_BROWSER" ] && open "$URL"
  exit 0
fi

if [ ! -x .venv/bin/python ]; then
  echo "No Python environment found at .venv — set the project up first (see README)."
  read -r -n1 -p "Press any key to close."
  exit 1
fi

echo "Starting Vāgdhenu… (loading the model takes about a minute)"
echo "Log: $PWD/$LOG"
GRADIO_SERVER_NAME="$HOST" GRADIO_SERVER_PORT="$PORT" nohup .venv/bin/python demo/app.py >"$LOG" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID >"$PID_FILE"
disown
# keep the Mac from sleeping (while on power) for as long as the studio runs
nohup caffeinate -s -w "$SERVER_PID" >/dev/null 2>&1 &
disown

for _ in $(seq 1 150); do
  if curl -s -o /dev/null --max-time 2 "$URL"; then
    echo "Ready → $URL"
    if [ "$HOST" = "0.0.0.0" ]; then
      IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)"
      echo "On your phone (same Wi-Fi): http://$IP:$PORT"
    fi
    [ -z "$VAGDHENU_NO_BROWSER" ] && open "$URL"
    echo "You can close this window; the studio keeps running in the background."
    exit 0
  fi
  if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo
    echo "The studio stopped while starting. Last lines of the log:"
    tail -n 25 "$LOG"
    read -r -n1 -p "Press any key to close."
    exit 1
  fi
  printf "."
  sleep 2
done
echo
echo "Still starting after 5 minutes — check $LOG"
read -r -n1 -p "Press any key to close."
