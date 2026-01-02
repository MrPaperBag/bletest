#!/data/data/com.termux/files/usr/bin/bash

# Directory where this script lives
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

PULL_FILE="$BASE_DIR/shouldipull"
START_FILE="$BASE_DIR/shouldistart"
APP_CMD="$BASE_DIR/start_server.sh"

cd "$BASE_DIR" || exit 1

# Ensure control files exist (defaults = yes)
[ -f "$START_FILE" ] || echo "yes" > "$START_FILE"
[ -f "$PULL_FILE" ]  || echo "yes" > "$PULL_FILE"

echo "[runner] started in $BASE_DIR"

while true; do
    SHOULD_START=$(cat "$START_FILE")

    if [ "$SHOULD_START" != "yes" ]; then
        sleep 5
        continue
    fi

    SHOULD_PULL=$(cat "$PULL_FILE")

    if [ "$SHOULD_PULL" = "yes" ]; then
        echo "[runner] git pull..."
        cd "$BASE_DIR/app" || exit 1
        git pull
        cd "$BASE_DIR"
        echo "no" > "$PULL_FILE"
    fi

    echo "[runner] starting app..."
    bash "$APP_CMD"

    echo "[runner] app exited, restarting..."
    sleep 2
done
