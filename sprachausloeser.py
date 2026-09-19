#!/usr/bin/env python3
"""
Sprachauslöser für Capture One  —  macOS + Windows
====================================================

Sagt man "Capture One auslösen", wird in Capture One eine Aufnahme
ausgelöst. Läuft offline, keine Cloud, keine Bestätigung, keine Taste.

HIER IST NICHTS ANZUPASSEN. Das Skript sucht das Vosk-Modell selbst
und funktioniert unabhängig davon, in welchem Ordner es liegt.

------------------------------------------------------------------
EINMALIGE VORBEREITUNG
------------------------------------------------------------------
1) Pakete installieren:
       pip install "vosk==0.3.44" sounddevice
   ACHTUNG: Die 0.3.44 ist wichtig. Ab 0.3.45 gibt es keine
   macOS-Pakete mehr.

2) Deutsches Modell herunterladen und entpacken — irgendwohin,
   der Ordner "vosk-model-small-de-0.15" wird automatisch gefunden,
   solange er neben diesem Skript, in ~/sprachausloeser, auf dem
   Schreibtisch oder in ~/Downloads liegt:
       https://alphacephei.com/vosk/models

3) In Capture One:
       Bearbeiten > Tastaturkürzel bearbeiten
       -> Set duplizieren (das Original ist schreibgeschützt)
       -> Befehl "Aufnahme" suchen
       -> GENAU DIESES KÜRZEL vergeben:
              Mac:     Cmd + Alt + Shift + A
              Windows: Strg + Alt + Shift + A

4) Starten:
       python3 sprachausloeser.py

   Geräteliste anzeigen:
       python3 sprachausloeser.py --devices

   Beenden mit Strg + C.
"""

import glob
import json
import os
import platform
import queue
import subprocess
import sys
import time

import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# =================================================================
# Auslöse-Phrasen
# Bewusst zweiteilig: ein einzelnes "auslösen" fällt im Gespräch
# ständig und würde ungewollt Fotos machen.
# =================================================================
TRIGGER_PHRASES = [
    "capture one auslösen",
    "capture one aufnahme",
]

COOLDOWN = 2.0        # Sekunden Sperrzeit nach einer Auslösung
INPUT_DEVICE = None   # None = Standardmikrofon. Oder Gerätenummer aus --devices.

# Kürzel, das in Capture One für "Aufnahme" hinterlegt sein muss
MAC_KEY = "a"
MAC_MODIFIERS = "option down, shift down"
WIN_SHORTCUT = "ctrl+alt+shift+a"

MAC_APP_HINT = "Capture One"
WIN_PROCESS = "Capture One.exe"


# =================================================================
# Modell automatisch finden
# =================================================================

def find_model():
    """Sucht den entpackten Vosk-Modellordner an den üblichen Orten."""
    env = os.environ.get("VOSK_MODEL", "").strip()
    if env:
        if os.path.isdir(env):
            return env
        sys.exit(f"VOSK_MODEL zeigt auf einen Ordner, den es nicht gibt:\n  {env}")

    here = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")

    # Reihenfolge: neben dem Skript, dann die üblichen Ablageorte.
    patterns = [
        os.path.join(here, "vosk-model-*"),
        os.path.join(here, "*", "vosk-model-*"),
        os.path.join(home, "sprachausloeser", "vosk-model-*"),
        os.path.join(home, "Desktop", "vosk-model-*"),
        os.path.join(home, "Desktop", "*", "vosk-model-*"),
        os.path.join(home, "Downloads", "vosk-model-*"),
        os.path.join(home, "vosk-model-*"),
    ]

    found = []
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            # Ein entpacktes Modell enthält immer einen "am"- oder "conf"-Ordner.
            if os.path.isdir(path) and (
                os.path.isdir(os.path.join(path, "am"))
                or os.path.isdir(os.path.join(path, "conf"))
            ):
                found.append(path)

    if not found:
        sys.exit(
            "Kein Vosk-Modell gefunden. Gesucht wurde in:\n  "
            + "\n  ".join(patterns)
            + "\n\nModell herunterladen und entpacken:\n"
            "  https://alphacephei.com/vosk/models\n"
            "  (vosk-model-small-de-0.15 reicht völlig)\n\n"
            "Liegt es woanders, den Pfad so übergeben:\n"
            '  VOSK_MODEL="/pfad/zum/modell" python3 sprachausloeser.py'
        )

    # Deutsche Modelle bevorzugen, falls mehrere da sind.
    german = [p for p in found if "-de" in os.path.basename(p)]
    return (german or found)[0]


# =================================================================
# Auslösen
# =================================================================

if IS_MAC:

    def _play(sound):
        subprocess.Popen(["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    beep_ok = lambda: _play("Glass")
    beep_fail = lambda: _play("Basso")

    def fire():
        script = (
            f'tell application "{MAC_APP_HINT}" to activate\n'
            f"delay 0.2\n"
            f'tell application "System Events" to '
            f'keystroke "{MAC_KEY}" using {{{MAC_MODIFIERS}}}'
        )
        res = subprocess.run(["osascript", "-e", script],
                             capture_output=True, text=True)
        if res.returncode != 0:
            print("  !! ", res.stderr.strip())
            beep_fail()
            return False
        beep_ok()
        return True

elif IS_WINDOWS:
    import winsound
    import keyboard
    import win32gui
    import win32process
    import psutil

    beep_ok = lambda: winsound.Beep(1200, 120)
    beep_fail = lambda: winsound.Beep(300, 400)

    def _is_front():
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name().lower() == WIN_PROCESS.lower()
        except Exception:
            return False

    def _focus():
        hits = []

        def _enum(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and \
               MAC_APP_HINT.lower() in win32gui.GetWindowText(hwnd).lower():
                hits.append(hwnd)

        win32gui.EnumWindows(_enum, None)
        if not hits:
            return False
        try:
            win32gui.ShowWindow(hits[0], 9)
            keyboard.press_and_release("alt")
            win32gui.SetForegroundWindow(hits[0])
            time.sleep(0.25)
            return True
        except Exception:
            return False

    def fire():
        if not _is_front() and not _focus():
            print("  !! Capture One nicht gefunden.")
            beep_fail()
            return False
        keyboard.send(WIN_SHORTCUT)
        beep_ok()
        return True

else:
    sys.exit("Dieses Skript läuft nur unter macOS oder Windows.")


# =================================================================

def list_devices():
    print("Verfügbare Eingabegeräte:\n")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i:2}] {d['name']}  "
                  f"({d['max_input_channels']} Kanäle, "
                  f"{int(d['default_samplerate'])} Hz)")
    print("\nNummer oben bei INPUT_DEVICE eintragen, "
          "oder None für das Standardgerät.")


def pick_samplerate(device):
    """Nimmt 16000, wenn das Gerät es kann — sonst dessen eigene Rate."""
    for rate in (16000, 48000, 44100):
        try:
            sd.check_input_settings(device=device, samplerate=rate,
                                    channels=1, dtype="int16")
            return rate
        except Exception:
            continue
    info = sd.query_devices(device, "input") if device is not None \
        else sd.query_devices(kind="input")
    return int(info["default_samplerate"])


def main():
    SetLogLevel(-1)

    model_path = find_model()
    samplerate = pick_samplerate(INPUT_DEVICE)

    info = sd.query_devices(INPUT_DEVICE, "input") if INPUT_DEVICE is not None \
        else sd.query_devices(kind="input")

    print(f"Sprachauslöser aktiv  ({platform.system()})")
    print(f"  Modell:    {os.path.basename(model_path)}")
    print(f"  Mikrofon:  {info['name']}")
    print(f"  Abtastung: {samplerate} Hz")
    print(f"  Phrasen:   " + "  |  ".join(TRIGGER_PHRASES))
    print("\nBeenden mit Strg+C\n")

    model = Model(model_path)
    grammar = json.dumps(TRIGGER_PHRASES + ["[unk]"], ensure_ascii=False)
    rec = KaldiRecognizer(model, samplerate, grammar)
    rec.SetWords(False)

    audio_q = queue.Queue()

    def callback(indata, frames, t, status):
        if status:
            print(status, file=sys.stderr)
        audio_q.put(bytes(indata))

    last_fire = 0.0

    with sd.RawInputStream(samplerate=samplerate, blocksize=4000,
                           dtype="int16", channels=1,
                           device=INPUT_DEVICE, callback=callback):
        while True:
            data = audio_q.get()

            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "").strip()
            else:
                text = json.loads(rec.PartialResult()).get("partial", "").strip()

            if not text:
                continue

            if any(p in text for p in TRIGGER_PHRASES):
                now = time.time()
                if now - last_fire < COOLDOWN:
                    continue
                last_fire = now
                print(f"[{time.strftime('%H:%M:%S')}] '{text}' -> auslösen")
                fire()
                rec.Reset()


if __name__ == "__main__":
    if "--devices" in sys.argv:
        list_devices()
        sys.exit(0)
    try:
        main()
    except KeyboardInterrupt:
        print("\nBeendet.")
