#!/bin/bash
# Double-click to run the Vāgdhenu studio so phones/tablets on the SAME Wi-Fi can use it too.
# Anyone on that Wi-Fi network can open it — use this at home, not on public Wi-Fi.
# The Mac stays awake while the studio runs, as long as it is plugged in.
cd "$(dirname "$0")" || exit 1
PORT="${VAGDHENU_PORT:-7860}"
# restart if it is currently running in Mac-only mode
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | grep -q "127.0.0.1:$PORT"; then
  echo "Restarting in phone mode…"
  ./"Stop Vagdhenu.command" </dev/null >/dev/null
  sleep 1
fi
VAGDHENU_HOST=0.0.0.0 exec ./"Start Vagdhenu.command"
