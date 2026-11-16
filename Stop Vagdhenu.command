#!/bin/bash
# Double-click in Finder to stop the Vāgdhenu chant studio started by "Start Vagdhenu.command".
# Chants waiting in the render queue are kept and resume on the next start.
cd "$(dirname "$0")" || exit 1

PORT="${VAGDHENU_PORT:-7860}"
PID_FILE="out/logs/server.pid"

PIDS=""
[ -f "$PID_FILE" ] && PIDS="$(cat "$PID_FILE")"
# also whatever is serving the port (e.g. started some other way)
PIDS="$PIDS $(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null)"

STOPPED=0
for p in $PIDS; do
  if kill -0 "$p" 2>/dev/null; then
    kill "$p" && STOPPED=1
  fi
done
rm -f "$PID_FILE"

if [ "$STOPPED" = 1 ]; then
  echo "Vāgdhenu stopped."
else
  echo "Vāgdhenu was not running."
fi
sleep 2
