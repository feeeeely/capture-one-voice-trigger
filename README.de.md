# Sprachauslöser für Capture One

*[English version](README.md)*

Freihändig auslösen per Sprachbefehl. Du sagst **„Capture One auslösen"**, die Kamera löst aus.

Gedacht für Reprografie, Buchdigitalisierung und Objektfotografie — überall dort, wo beide Hände am Objekt sind und der Weg zur Tastatur stört.

Läuft vollständig offline. Keine Cloud, kein Konto, keine Internetverbindung im Betrieb.

---

## Voraussetzungen

- macOS
- Capture One (Pro oder CH) mit funktionierendem Tethering
- Python 3.10 oder neuer — [hier herunterladen](https://www.python.org/downloads/), falls nicht vorhanden

Beim Installieren von Python nichts einstellen, die Standardwerte genügen.

---

## Einrichtung

**1. Dieses Repository herunterladen**

Oben auf `Code` → `Download ZIP`, dann entpacken. Der Ordner kann liegen, wo du willst.

**2. Installation starten**

Rechtsklick auf den entpackten Ordner → „Neues Terminal beim Ordner". Dann eintippen:

```
bash setup.sh
```

Das dauert ein paar Minuten. Es lädt die Spracherkennung herunter (ca. 45 MB) und richtet alles ein.

**3. Kürzel in Capture One anlegen**

`Bearbeiten` → `Tastaturkürzel bearbeiten`

- Oben das Standard-Set **duplizieren** (das Original lässt sich nicht ändern)
- **Wichtig:** Oben im Auswahlmenü auf dein neues Set umschalten. Wird das vergessen, passiert später nichts.
- Befehl **„Aufnahme"** suchen (Kategorie *Kamera*) und das Kürzel **Option + Shift + A** vergeben

Zum Prüfen: Das Kürzel einmal von Hand drücken. Löst die Kamera nicht aus, stimmt etwas an dieser Stelle nicht — dann hilft auch das Skript nicht weiter.

**4. Starten**

Doppelklick auf **`start.command`**

Beim ersten Start fragt macOS zweimal nach Berechtigungen:

- **Mikrofon** — erlauben
- **Bedienungshilfen** — erlauben, danach das Terminal schließen und `start.command` erneut starten

Das Fenster muss geöffnet bleiben, solange du den Sprachauslöser benutzt. Beenden mit `Strg + C` oder durch Schließen des Fensters.

---

## Benutzung

Capture One in den Vordergrund holen, dann sprechen:

> **„Capture One auslösen"**

Ein heller Ton bestätigt die Auslösung, ein tiefer meldet einen Fehler. Im Fenster erscheint zusätzlich, was erkannt wurde.

Die Phrase ist bewusst zweiteilig. Ein einzelnes „auslösen" würde im Gespräch ständig fehlauslösen.

---

## Wenn etwas nicht klappt

**„Es hört mich, aber es passiert nichts"**
Das Kürzel kommt nicht an. Drück Option + Shift + A von Hand in Capture One. Passiert dabei nichts, ist entweder das duplizierte Set nicht ausgewählt oder keine Kamera verbunden.

**„osascript is not allowed to send keystrokes"**
Die Bedienungshilfen fehlen. Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen → Terminal aktivieren. Terminal danach komplett beenden (Cmd + Q) und neu starten, sonst greift die Änderung nicht.

**„Es hört mich gar nicht"**
Falsches Mikrofon. Im Terminal sehen, welches benutzt wird:

```
./venv/bin/python sprachausloeser.py --devices
```

Dann in `sprachausloeser.py` die Zeile `INPUT_DEVICE = None` auf die gewünschte Nummer ändern.

**Anderes Tastenkürzel gewünscht**
In `sprachausloeser.py` die Zeilen `MAC_KEY` und `MAC_MODIFIERS` anpassen. Mögliche Modifikatoren: `command down`, `option down`, `shift down`, `control down`.

**Eigene Auslösephrase**
Die Liste `TRIGGER_PHRASES` in `sprachausloeser.py` ändern. Nur Kleinbuchstaben verwenden. Zwei Wörter oder mehr nehmen, sonst häufen sich Fehlauslösungen.

---

## Wie es funktioniert

Das Skript hört durchgehend am Mikrofon mit und vergleicht das Gehörte mit einer kurzen, festen Wortliste. Bei einem Treffer sendet es das Tastenkürzel an Capture One — genau so, als hättest du es selbst gedrückt. Capture One merkt keinen Unterschied.

Die Spracherkennung übernimmt [Vosk](https://alphacephei.com/vosk/) mit einem kleinen deutschen Modell. Weil nur zwischen zwei festen Phrasen unterschieden werden muss, ist die Trefferquote auch bei Umgebungsgeräuschen hoch und die Verzögerung liegt unter einer Sekunde.

---

## Grenzen

- **Nur macOS getestet.** Der Windows-Teil ist im Code vorhanden, aber ungeprüft. Rückmeldungen willkommen.
- **Nur Deutsch.** Für andere Sprachen ein passendes [Vosk-Modell](https://alphacephei.com/vosk/models) in den Ordner legen und `TRIGGER_PHRASES` anpassen. Der Rest funktioniert unverändert.
- **Capture One muss im Vordergrund sein.** Das Skript holt es selbst nach vorn, bei mehreren Fenstern kann es aber das falsche erwischen.
- **Vosk ist auf 0.3.44 festgelegt.** Ab 0.3.45 gibt es keine macOS-Pakete mehr. Nicht erhöhen.

---

## Was es nicht ist

Kein Sprachassistent. Es versteht genau eine Anweisung und macht sonst nichts. Das ist Absicht: Ein Sprachmodell dazwischen würde mehrere Sekunden kosten, eine Bestätigung verlangen und gelegentlich etwas anderes tun als gewünscht. Für einen Auslöser ist das untauglich.

Wer Capture One weitergehend steuern will — Varianten, Ebenen, Ausgabe —, findet das bei [capture-one-mcp](https://glama.ai/mcp/servers/byjustinjones/capture-one-mcp). Tethered Capture ist dort ausdrücklich nicht enthalten, insofern ergänzen sich beide.

---

## Lizenz

MIT
# capture-one-sprachausloeser
