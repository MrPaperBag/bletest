#!/data/data/com.termux/files/usr/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$BASE_DIR/app" || exit 1
python3 app.py
