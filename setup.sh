#!/bin/bash
# Einrichtung für den Sprachauslöser. Einmal ausführen, dann fertig.
set -e

cd "$(dirname "$0")"

echo "Sprachauslöser für Capture One — Einrichtung"
echo "============================================"
echo

# --- 1. macOS prüfen ------------------------------------------------
if [ "$(uname)" != "Darwin" ]; then
    echo "FEHLER: Dieses Installationsskript ist für macOS."
    echo "Für Windows siehe README."
    exit 1
fi

# --- 2. Passendes Python finden -------------------------------------
# Mindestens 3.10, weil cffi darunter keine Intel-Mac-Pakete hat.
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
    echo "FEHLER: Es wird Python 3.10 oder neuer benötigt."
    echo
    echo "Das mit macOS gelieferte Python ist zu alt."
    echo "Installiere eine aktuelle Version von:"
    echo "    https://www.python.org/downloads/"
    echo "und führe dieses Skript danach erneut aus."
    exit 1
fi

echo "Python gefunden: $($PY --version)"

# --- 3. Virtuelle Umgebung ------------------------------------------
if [ ! -d "venv" ]; then
    echo "Lege virtuelle Umgebung an..."
    "$PY" -m venv venv
fi

echo "Installiere Pakete..."
./venv/bin/pip install --quiet --upgrade pip
# vosk 0.3.44 ist die letzte Version mit macOS-Paketen. NICHT erhöhen.
./venv/bin/pip install --quiet "vosk==0.3.44" sounddevice

# --- 4. Sprachmodell ------------------------------------------------
MODEL="vosk-model-small-de-0.15"
if [ ! -d "$MODEL" ]; then
    echo "Lade deutsches Sprachmodell (ca. 45 MB)..."
    curl -fL# -o model.zip "https://alphacephei.com/vosk/models/${MODEL}.zip"
    unzip -q model.zip
    rm model.zip
else
    echo "Sprachmodell bereits vorhanden."
fi

chmod +x start.command 2>/dev/null || true

echo
echo "============================================"
echo "Fertig."
echo
echo "NOCH ZU TUN in Capture One:"
echo "  Bearbeiten > Tastaturkürzel bearbeiten"
echo "  -> Set duplizieren und oben AUSWÄHLEN"
echo "  -> Befehl 'Aufnahme' das Kürzel geben:  Option + Shift + A"
echo
echo "Dann starten mit einem Doppelklick auf:  start.command"
echo "============================================"
