#!/usr/bin/env python3
"""
Voice Trigger for Capture One  —  macOS + Windows
==================================================

Say "Capture One take a photo" and the tethered camera fires.
Runs fully offline. No cloud, no account, no confirmation click.

NOTHING NEEDS EDITING HERE. The script locates the Vosk model on its
own and works regardless of which folder it lives in.

--------------------------------------------------------------------
ONE-TIME SETUP
--------------------------------------------------------------------
1) Install the packages:
       pip install "vosk==0.3.44" sounddevice
   The 0.3.44 pin matters. From 0.3.45 onwards there are no macOS
   wheels. Do not bump it.

2) Download a Vosk model and unzip it anywhere near this script —
   next to it, in ~/Downloads, or on the Desktop. Any folder starting
   with "vosk-model-" is found automatically.
       https://alphacephei.com/vosk/models

3) In Capture One:
       Edit > Edit Keyboard Shortcuts
       -> Duplicate the default set, then SELECT it in the dropdown
       -> Find the "Capture" command (category: Camera)
       -> Assign exactly this shortcut:
              macOS:   Option + Shift + A
              Windows: Ctrl + Alt + Shift + A

4) Run it:
       python3 voice_trigger.py

   List microphones:
       python3 voice_trigger.py --devices

   Show recognition diagnostics (useful when changing phrases):
       python3 voice_trigger.py --verbose

   Quit with Ctrl + C.
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

# ====================================================================
# Trigger phrases
#
# Any of these fires the shutter. Lowercase only, no punctuation.
# Use two words or more — a single word causes constant false
# triggers during normal conversation.
#
# Every word must exist in your model's vocabulary. Unknown words are
# skipped silently, so run with --verbose after changing these and
# watch for "missing in vocabulary" warnings.
# ====================================================================
TRIGGER_PHRASES = [
    "capture one take a photo",
    "capture one shoot",
]

COOLDOWN = 2.0        # seconds of lockout after a shot
INPUT_DEVICE = None   # None = system default. Or a number from --devices.

# Must match the shortcut assigned in Capture One
MAC_KEY = "a"
MAC_MODIFIERS = "option down, shift down"
WIN_SHORTCUT = "ctrl+alt+shift+a"

APP_HINT = "Capture One"
WIN_PROCESS = "Capture One.exe"


# ====================================================================
# Locate the speech model
# ====================================================================

def find_model():
    """Find an unpacked Vosk model folder in the usual places."""
    env = os.environ.get("VOSK_MODEL", "").strip()
    if env:
        if os.path.isdir(env):
            return env
        sys.exit(f"VOSK_MODEL points to a folder that does not exist:\n  {env}")

    here = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")

    patterns = [
        os.path.join(here, "vosk-model-*"),
        os.path.join(here, "*", "vosk-model-*"),
        os.path.join(home, "Downloads", "vosk-model-*"),
        os.path.join(home, "Desktop", "vosk-model-*"),
        os.path.join(home, "Desktop", "*", "vosk-model-*"),
        os.path.join(home, "vosk-model-*"),
    ]

    found = []
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            # An unpacked model always contains an "am" or "conf" folder.
            if os.path.isdir(path) and (
                os.path.isdir(os.path.join(path, "am"))
                or os.path.isdir(os.path.join(path, "conf"))
            ):
                if path not in found:
                    found.append(path)

    if not found:
        sys.exit(
            "No Vosk model found. Looked in:\n  "
            + "\n  ".join(patterns)
            + "\n\nDownload one and unzip it next to this script:\n"
            "  https://alphacephei.com/vosk/models\n"
            "  (the small models are plenty)\n\n"
            "If it lives elsewhere, point at it directly:\n"
            '  VOSK_MODEL="/path/to/model" python3 voice_trigger.py'
        )

    if len(found) > 1:
        print("Several models found — using the first:")
        for p in found:
            print(f"    {os.path.basename(p)}")
        print("  Set VOSK_MODEL to choose explicitly.\n")

    return found[0]


# ====================================================================
# Firing the shutter
# ====================================================================

if IS_MAC:

    def _play(sound):
        subprocess.Popen(["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def beep_ok():
        _play("Glass")

    def beep_fail():
        _play("Basso")

    def fire():
        script = (
            f'tell application "{APP_HINT}" to activate\n'
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

    def beep_ok():
        winsound.Beep(1200, 120)

    def beep_fail():
        winsound.Beep(300, 400)

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
               APP_HINT.lower() in win32gui.GetWindowText(hwnd).lower():
                hits.append(hwnd)

        win32gui.EnumWindows(_enum, None)
        if not hits:
            return False
        try:
            win32gui.ShowWindow(hits[0], 9)          # SW_RESTORE
            keyboard.press_and_release("alt")        # beat the foreground lock
            win32gui.SetForegroundWindow(hits[0])
            time.sleep(0.25)
            return True
        except Exception:
            return False

    def fire():
        if not _is_front() and not _focus():
            print("  !! Capture One not found.")
            beep_fail()
            return False
        keyboard.send(WIN_SHORTCUT)
        beep_ok()
        return True

else:
    sys.exit("This script runs on macOS and Windows only.")


# ====================================================================

def list_devices():
    print("Available input devices:\n")
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(f"  [{i:2}] {d['name']}  "
                  f"({d['max_input_channels']} channels, "
                  f"{int(d['default_samplerate'])} Hz)")
    print("\nPut the number into INPUT_DEVICE above, "
          "or leave None for the system default.")


def pick_samplerate(device):
    """Use 16000 if the device supports it, otherwise its own rate."""
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


def main(verbose=False):
    # Verbose surfaces "missing in vocabulary" warnings, which is the
    # only way to tell why a phrase never matches.
    SetLogLevel(0 if verbose else -1)

    model_path = find_model()
    samplerate = pick_samplerate(INPUT_DEVICE)

    info = sd.query_devices(INPUT_DEVICE, "input") if INPUT_DEVICE is not None \
        else sd.query_devices(kind="input")

    print(f"Voice Trigger active  ({platform.system()})")
    print(f"  Model:      {os.path.basename(model_path)}")
    print(f"  Microphone: {info['name']}")
    print(f"  Sample rate:{samplerate} Hz")
    print(f"  Phrases:    " + "  |  ".join(TRIGGER_PHRASES))
    print("\nQuit with Ctrl+C\n")

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
                # Partial results react faster once the phrase is complete.
                text = json.loads(rec.PartialResult()).get("partial", "").strip()

            if not text:
                continue

            if verbose:
                print(f"    heard: {text}")

            if any(p in text for p in TRIGGER_PHRASES):
                now = time.time()
                if now - last_fire < COOLDOWN:
                    continue
                last_fire = now
                print(f"[{time.strftime('%H:%M:%S')}] '{text}' -> firing")
                fire()
                rec.Reset()


if __name__ == "__main__":
    if "--devices" in sys.argv:
        list_devices()
        sys.exit(0)
    try:
        main(verbose="--verbose" in sys.argv)
    except KeyboardInterrupt:
        print("\nStopped.")
