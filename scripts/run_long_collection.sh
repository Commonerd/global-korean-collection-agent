#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
mkdir -p data/logs

: "${MODE:=production}"
: "${DRY_RUN:=false}"
: "${ENABLE_PLACES:=true}"
: "${ITERATIONS:=12}"
: "${COLLECTION_GOAL:=Global Korean business}"
: "${COLLECTION_GOALS:=$COLLECTION_GOAL}"
: "${MAX_DEPTH:=4}"
: "${MAX_REQUESTS_PER_RUN:=120}"
: "${MAX_REQUESTS_PER_DOMAIN:=12}"
: "${MAX_NEW_ENTITIES_PER_RUN:=50}"
: "${MAX_RUNTIME_SECONDS:=1800}"
export MODE DRY_RUN ENABLE_PLACES
export MAX_DEPTH MAX_REQUESTS_PER_RUN MAX_REQUESTS_PER_DOMAIN
export MAX_NEW_ENTITIES_PER_RUN MAX_RUNTIME_SECONDS

PYTHON=${PYTHON:-"$ROOT_DIR/.venv/bin/python"}

OLD_IFS=$IFS
IFS=,
set -- $COLLECTION_GOALS
IFS=$OLD_IFS
for goal in "$@"; do
    [ -n "$goal" ] || continue
    echo "[SCHEDULER] goal=$goal iterations=$ITERATIONS"
    "$PYTHON" -m agent.main \
      --mode loop \
      --iterations "$ITERATIONS" \
      --goal "$goal"
done
