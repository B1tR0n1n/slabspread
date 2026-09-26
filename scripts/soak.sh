#!/usr/bin/env bash
# Run the ingestion scheduler as a soak: own DB, own raw dir, PID file, explicit environment.
#   scripts/soak.sh start | stop | restart | status
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOAK="$ROOT/soak"; PIDF="$SOAK/scheduler.pid"; LOG="$SOAK/scheduler.log"
export SLABSPREAD_AUTH_MODE=off SLABSPREAD_DEBUG=1
export SLABSPREAD_DATABASE_URL="sqlite:///$SOAK/soak.db" SLABSPREAD_RAW_DIR="$SOAK/raw"
export SLABSPREAD_POLYGON_BACKFILL_BLOCKS="${SLABSPREAD_POLYGON_BACKFILL_BLOCKS:-4000}"

alive() { [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; }

case "${1:-status}" in
  start)
    if alive; then echo "already running (pid $(cat "$PIDF"))"; exit 0; fi
    mkdir -p "$SOAK"
    "$ROOT/.venv/bin/alembic" -q upgrade head
    [ -f "$SOAK/started_at" ] || date -u +"%Y-%m-%dT%H:%M:%SZ" > "$SOAK/started_at"
    nohup "$ROOT/.venv/bin/python" -m ingest.scheduler >> "$LOG" 2>&1 &
    echo $! > "$PIDF"; sleep 2
    alive && echo "started pid $(cat "$PIDF") on $SLABSPREAD_DATABASE_URL" || { echo "failed to start; see $LOG"; exit 1; }
    ;;
  stop)
    if alive; then kill "$(cat "$PIDF")"; sleep 1; echo "stopped"; else echo "not running"; fi
    rm -f "$PIDF"
    ;;
  restart) "$0" stop; "$0" start ;;
  status)
    if alive; then echo "running pid $(cat "$PIDF") since $(cat "$SOAK/started_at" 2>/dev/null || echo '?')"; else echo "not running"; fi
    [ -f "$SOAK/soak.db" ] && "$ROOT/.venv/bin/python" - <<PY
import sqlite3; c = sqlite3.connect("$SOAK/soak.db")
print("runs:", c.execute("select source_key,status,count(*) from ingest_runs group by 1,2").fetchall())
print("events:", c.execute("select source_key,count(*) from onchain_events group by 1").fetchall(),
      "| listings", c.execute("select count(*) from listings").fetchone()[0],
      "| packs", c.execute("select count(*) from packs").fetchone()[0])
PY
    ;;
  *) echo "usage: $0 start|stop|restart|status"; exit 2 ;;
esac
