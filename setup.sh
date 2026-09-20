#!/bin/bash
# One-time setup for Voice Trigger. Run once, then you're done.
set -e

cd "$(dirname "$0")"

echo "Voice Trigger for Capture One — setup"
echo "====================================="
echo

# --- 1. macOS check -------------------------------------------------
if [ "$(uname)" != "Darwin" ]; then
    echo "ERROR: this installer is for macOS."
    echo "For Windows, see the README."
    exit 1
fi

# --- 2. Find a suitable Python --------------------------------------
# 3.10 minimum: cffi publishes no Intel-Mac wheels below that.
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
            PY="$candidate"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "ERROR: Python 3.10 or newer is required."
    echo
    echo "The Python that ships with macOS is too old."
    echo "Install a current version from:"
    echo "    https://www.python.org/downloads/"
    echo "then run this script again."
    exit 1
fi

echo "Found Python: $($PY --version)"

# --- 3. Virtual environment -----------------------------------------
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    "$PY" -m venv venv
fi

echo "Installing packages..."
./venv/bin/pip install --quiet --upgrade pip
# 0.3.44 is the last vosk release with macOS wheels. Do not bump.
./venv/bin/pip install --quiet "vosk==0.3.44" sounddevice

# --- 4. Speech model ------------------------------------------------
# Override with:  MODEL=vosk-model-small-de-0.15 bash setup.sh
MODEL="${MODEL:-vosk-model-small-en-us-0.15}"

if [ ! -d "$MODEL" ]; then
    echo "Downloading speech model $MODEL (~45 MB)..."
    curl -fL# -o model.zip "https://alphacephei.com/vosk/models/${MODEL}.zip"
    unzip -q model.zip
    rm model.zip
else
    echo "Speech model already present."
fi

chmod +x start.command 2>/dev/null || true

echo
echo "====================================="
echo "Done."
echo
echo "STILL TO DO in Capture One:"
echo "  Edit > Edit Keyboard Shortcuts"
echo "  -> Duplicate the default set, then SELECT it in the dropdown"
echo "  -> Give the 'Capture' command this shortcut:  Option + Shift + A"
echo
echo "Then double-click:  start.command"
echo "====================================="
