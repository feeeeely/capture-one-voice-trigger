#!/bin/bash
# Doppelklick startet den Sprachauslöser.
cd "$(dirname "$0")"

if [ ! -x "venv/bin/python" ]; then
    echo "Die Einrichtung fehlt noch."
    echo "Führe zuerst setup.sh aus (siehe README)."
    echo
    read -p "Zum Schließen Enter drücken."
    exit 1
fi

./venv/bin/python sprachausloeser.py
