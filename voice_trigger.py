#!/usr/bin/env python3
"""
Voice Trigger for Capture One  —  macOS + Windows
==================================================

Say "Capture One focus" and the tethered camera focuses.
Say "Capture One take a photo" and it fires.
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
       -> Assign exactly these shortcuts:

          Command                         macOS              Windows
          Capture                         Option+Shift+A     Ctrl+Alt+Shift+A
          Start/Stop Camera Autofocus     Option+Shift+F     Ctrl+Alt+Shift+F

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
# Voice commands
#
# Each command has its own phrases and its own keyboard shortcut.
# The shortcut must match what is assigned in Capture One.
#
# Phrases: lowercase only, no punctuation, two words or more — a
# single word causes constant false triggers during conversation.
#
# Every word must exist in your model's vocabulary. Unknown words are
# skipped silently, so run with --verbose after changing phrases and
# watch for "missing in vocabulary" warnings.
#
# Each command also has its own cooldown, so "focus" followed straight
# away by "take a photo" works, while an echo can't fire the same
# command twice.
# ====================================================================
COMMANDS = {
    "focus": {
        "phrases": ["capture one focus"],
        "mac_key": "f",
        "mac_modifiers": "option down, shift down",
        "win_shortcut": "ctrl+alt+shift+f",
        "cooldown": 1.5,
    },
    "capture": {
        "phrases": ["capture one take a photo", "capture one shoot"],
        "mac_key": "a",
        "mac_modifiers": "option down, shift down",
        "win_shortcut": "ctrl+alt+shift+a",
        "cooldown": 2.0,
    },
}

INPUT_DEVICE = None   # None = system default. Or a number from --devices.

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
# Sending the shortcut
# ====================================================================

if IS_MAC:

    # A different sound per command, so you know what happened
    # without looking at the screen.
    SOUNDS = {"focus": "Tink", "capture": "Glass", "error": "Basso"}

    def play(name):
        subprocess.Popen(
            ["afplay", f"/System/Library/Sounds/{SOUNDS.get(name, 'Glass')}.aiff"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def send(name, cmd):
        script = (
            f'tell application "{APP_HINT}" to activate\n'
            f"delay 0.2\n"
            f'tell application "System Events" to '
            f'keystroke "{cmd["mac_key"]}" using {{{cmd["mac_modifiers"]}}}'
        )
        res = subprocess.run(["osascript", "-e", script],
                             capture_output=True, text=True)
        if res.returncode != 0:
            print("  !! ", res.stderr.strip())
            play("error")
            return False
        play(name)
        return True

elif IS_WINDOWS:
    import winsound
    import keyboard
    import win32gui
    import win32process
    import psutil

    # (frequency Hz, duration ms)
    TONES = {"focus": (900, 80), "capture": (1200, 120), "error": (300, 400)}

    def play(name):
        winsound.Beep(*TONES.get(name, TONES["capture"]))

    def _is_front():
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name().lower() == WIN_PROCESS.lower()
        except Exception:
            return False

    def _focus_window():
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

    def send(name, cmd):
        if not _is_front() and not _focus_window():
            print("  !! Capture One not found.")
            play("error")
            return False
        keyboard.send(cmd["win_shortcut"])
        play(name)
        return True

else:
    sys.exit("This script runs on macOS and Windows only.")


# ====================================================================
# Matching
# ====================================================================

def match(text):
    """Return the name of the command whose phrase appears in text.

    If several match, the longest phrase wins — it's the most specific.
    """
    best, best_len = None, 0
    for name, cmd in COMMANDS.items():
        for phrase in cmd["phrases"]:
            if phrase in text and len(phrase) > best_len:
                best, best_len = name, len(phrase)
    return best


def all_phrases():
    return [p for cmd in COMMANDS.values() for p in cmd["phrases"]]


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
    print(f"  Model:       {os.path.basename(model_path)}")
    print(f"  Microphone:  {info['name']}")
    print(f"  Sample rate: {samplerate} Hz")
    print("  Commands:")
    for name, cmd in COMMANDS.items():
        print(f"    {name:8} " + "  |  ".join(cmd["phrases"]))
    print("\nQuit with Ctrl+C\n")

    model = Model(model_path)
    grammar = json.dumps(all_phrases() + ["[unk]"], ensure_ascii=False)
    rec = KaldiRecognizer(model, samplerate, grammar)
    rec.SetWords(False)

    audio_q = queue.Queue()

    def callback(indata, frames, t, status):
        if status:
            print(status, file=sys.stderr)
        audio_q.put(bytes(indata))

    last_fired = {name: 0.0 for name in COMMANDS}

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

            name = match(text)
            if name is None:
                continue

            now = time.time()
            if now - last_fired[name] < COMMANDS[name]["cooldown"]:
                continue
            last_fired[name] = now

            print(f"[{time.strftime('%H:%M:%S')}] '{text}' -> {name}")
            send(name, COMMANDS[name])
            rec.Reset()


if __name__ == "__main__":
    if "--devices" in sys.argv:
        list_devices()
        sys.exit(0)
    try:
        main(verbose="--verbose" in sys.argv)
    except KeyboardInterrupt:
        print("\nStopped.")
