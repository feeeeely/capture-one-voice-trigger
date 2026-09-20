#!/bin/bash
# Double-click to start the voice trigger.
cd "$(dirname "$0")"

if [ ! -x "venv/bin/python" ]; then
    echo "Setup has not been run yet."
    echo "Run setup.sh first (see README)."
    echo
    read -p "Press Enter to close."
    exit 1
fi

./venv/bin/python voice_trigger.py
