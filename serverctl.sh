#!/data/data/com.termux/files/usr/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

PULL_FILE="$BASE_DIR/shouldipull"
START_FILE="$BASE_DIR/shouldistart"

# Ensure files exist
[ -f "$START_FILE" ] || echo "yes" > "$START_FILE"
[ -f "$PULL_FILE" ]  || echo "yes" > "$PULL_FILE"

cmd="$1"
value="$2"

case "$cmd" in
    start)
        [ "$value" = "yes" ] || [ "$value" = "no" ] || {
            echo "Usage: serverctl start yes|no"
            exit 1
        }
        echo "$value" > "$START_FILE"
        ;;
    pull)
        [ "$value" = "yes" ] || [ "$value" = "no" ] || {
            echo "Usage: serverctl pull yes|no"
            exit 1
        }
        echo "$value" > "$PULL_FILE"
        ;;
    status)
        echo "shouldistart=$(cat "$START_FILE")"
        echo "shouldipull=$(cat "$PULL_FILE")"
        ;;
    *)
        echo "Usage:"
        echo "  serverctl start yes|no"
        echo "  serverctl pull  yes|no"
        echo "  serverctl status"
        exit 1
        ;;
esac
