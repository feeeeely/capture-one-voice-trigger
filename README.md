# Voice Trigger for Capture One

*[Deutsche Version](README.de.md)*

Hands-free tethered capture. Say **"Capture One take a photo"** and the camera fires.

Built for repro work, book digitisation and object photography — anywhere both hands are on the object and walking back to the keyboard breaks the shot.

Runs entirely offline. No cloud, no account, no internet connection while in use.

Works with Capture One Pro and Capture One CH.

---

## Requirements

- macOS
- Capture One (Pro or CH) with working tethering
- Python 3.10 or newer — [download here](https://www.python.org/downloads/) if you don't have it

The default options during the Python install are fine.

---

## Setup

**1. Download this repository**

Click `Code` → `Download ZIP`, then unzip it. The folder can live anywhere.

**2. Run the installer**

Right-click the unzipped folder → "New Terminal at Folder". Then type:

```
bash setup.sh
```

This takes a few minutes. It downloads the speech model (~45 MB) and sets everything up.

**2a. If macOS blocks it**

On first launch macOS may say:

> "start.command" cannot be opened because it is from an unidentified developer.

This is normal for anything outside the App Store. macOS flags every downloaded file regardless of its contents.

Run this once, in the same Terminal from step 2:

```
xattr -dr com.apple.quarantine .
```

The trailing dot matters — it means "this folder". Everything starts normally afterwards.

If that makes you uneasy: the full source is in this repository. For a program that listens to your microphone continuously and sends keystrokes, scepticism is warranted — read the code first, it's short.

**3. Assign the shortcut in Capture One**

`Edit` → `Edit Keyboard Shortcuts`

- **Duplicate** the default set (the original is read-only)
- **Important:** switch to your new set in the dropdown at the top. Forgetting this is the single most common failure.
- Find the **"Capture"** command (category *Camera*) and assign **Option + Shift + A**

Test it: press the shortcut by hand. If the camera doesn't fire, something is wrong here — the script won't help until it does.

**4. Start**

Double-click **`start.command`**

macOS asks for two permissions on first run:

- **Microphone** — allow
- **Accessibility** — allow, then close the Terminal window and launch `start.command` again

The window must stay open while you use the trigger. Quit with `Ctrl + C` or by closing the window.

---

## Usage

Bring Capture One to the front, then say either:

> **"Capture One take a photo"**
> **"Capture One shoot"**

A high tone confirms the shot, a low tone reports a failure. The window also logs what was recognised.

The phrases are deliberately several words long. A single "shoot" would fire constantly during normal conversation.

---

## Using another language

Two changes.

**1. Swap the model**

Download one for your language from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) — the small ones (~50 MB) are plenty, since the script only distinguishes between a couple of fixed phrases. Unzip it into the project folder and delete the English one.

For German, the installer can fetch it for you:

```
MODEL=vosk-model-small-de-0.15 bash setup.sh
```

**2. Change the trigger phrases**

Edit `TRIGGER_PHRASES` in `voice_trigger.py`:

```python
TRIGGER_PHRASES = [
    "capture one auslösen",
    "capture one foto",
]
```

Lowercase only, no punctuation. Two words or more.

Every word must exist in the model's vocabulary — unknown words are skipped silently, which looks exactly like the microphone not working. To check, run:

```
./venv/bin/python voice_trigger.py --verbose
```

That prints everything the recogniser hears plus any "missing in vocabulary" warnings.

Nothing else needs touching. The shortcut, the audio handling and the Capture One side are language-independent.

---

## Troubleshooting

**"From an unidentified developer"**
See step 2a. Run `xattr -dr com.apple.quarantine .` in the project folder.

**"It hears me but nothing happens"**
The keystroke isn't landing. Press Option + Shift + A by hand in Capture One. If nothing happens, either the duplicated shortcut set isn't selected or no camera is connected.

**"osascript is not allowed to send keystrokes"**
Accessibility permission is missing. System Settings → Privacy & Security → Accessibility → enable Terminal. Then quit Terminal completely (Cmd + Q) and restart — the change only takes effect on launch.

**"It doesn't hear me at all"**
Wrong microphone. List the available ones:

```
./venv/bin/python voice_trigger.py --devices
```

Then set `INPUT_DEVICE = None` in `voice_trigger.py` to the number you want.

**Different keyboard shortcut**
Edit `MAC_KEY` and `MAC_MODIFIERS` in `voice_trigger.py`. Available modifiers: `command down`, `option down`, `shift down`, `control down`.

---

## How it works

The script listens continuously and matches what it hears against a short, fixed word list. On a match it sends the keyboard shortcut to Capture One — exactly as if you had pressed it yourself. Capture One can't tell the difference.

Recognition is handled by [Vosk](https://alphacephei.com/vosk/). Because it only has to distinguish between two fixed phrases, accuracy stays high even with background noise, and latency is under a second.

---

## Limitations

- **Only tested on macOS.** Windows code is present but unverified. Reports welcome.
- **Capture One must be frontmost.** The script brings it forward itself, but with several windows open it may pick the wrong one.
- **Vosk is pinned to 0.3.44.** From 0.3.45 onwards there are no macOS wheels. Don't bump it.
- **Python 3.10 minimum.** `cffi` publishes no Intel-Mac wheels for 3.9, which is what macOS ships as the system Python.

---

## What this is not

Not a voice assistant. It understands exactly one instruction and does nothing else. That's deliberate: putting a language model in the loop would cost several seconds, require a confirmation click, and occasionally do something other than what you asked. For a shutter release that's useless.

If you want broader control over Capture One — variants, layers, output — see [capture-one-mcp](https://glama.ai/mcp/servers/byjustinjones/capture-one-mcp). Tethered capture is explicitly out of scope there, so the two complement each other.

---

## License

MIT

---

## Acknowledgements

Speech recognition by [Vosk](https://alphacephei.com/vosk/), Apache 2.0.
The English model `vosk-model-small-en-us-0.15` is Apache 2.0 as well. If you
swap in a different one, check the licence column on the
[model list](https://alphacephei.com/vosk/models) — not all of them are permissive.

## Disclaimer

Not affiliated with, endorsed by, or supported by Capture One A/S. "Capture One"
is their trademark, used here only to describe what this tool works with.

This is an independent program. It contains no Capture One code and changes
nothing inside the application — it sends a keyboard shortcut, exactly as a foot
pedal or a macro pad would.
