# Sprachauslöser für Capture One

*[English version](README.md)*

Freihändig scharfstellen und auslösen per Sprachbefehl. Du sagst **„Capture One focus"**, die Kamera stellt scharf — **„Capture One take a photo"**, sie löst aus.

Gedacht für Reprografie, Buchdigitalisierung und Objektfotografie — überall dort, wo beide Hände am Objekt sind und der Weg zur Tastatur stört.

Läuft vollständig offline. Keine Cloud, kein Konto, keine Internetverbindung im Betrieb.

Funktioniert mit Capture One Pro und Capture One CH.

> **Hinweis:** Die Spracherkennung läuft standardmäßig auf Englisch, weil das Projekt international nutzbar sein soll. Wie du auf deutsche Befehle umstellst, steht weiter unten unter [Auf Deutsch umstellen](#auf-deutsch-umstellen) — das sind zwei Handgriffe.

---

## Voraussetzungen

- macOS, oder Windows (siehe Hinweis unter Grenzen)
- Capture One (Pro oder CH) mit funktionierendem Tethering
- Python 3.10 oder neuer — [hier herunterladen](https://www.python.org/downloads/), falls nicht vorhanden

Beim Installieren von Python nichts einstellen, die Standardwerte genügen.

---

## Einrichtung

**1. Dieses Repository herunterladen**

Oben auf `Code` → `Download ZIP`, dann entpacken. Der Ordner kann liegen, wo du willst.

**2. Installation starten**

*Unter macOS:* Rechtsklick auf den entpackten Ordner → „Neues Terminal beim Ordner", dann eintippen:

```
bash setup.sh
```

*Unter Windows:* Doppelklick auf **`setup.bat`**.

In beiden Fällen dauert es ein paar Minuten. Es lädt die Spracherkennung herunter (ca. 45 MB) und richtet alles ein.

Wenn du von vornherein deutsche Befehle willst, stattdessen:

```
MODEL=vosk-model-small-de-0.15 bash setup.sh
```

**2a. Falls macOS die Ausführung blockiert** *(nur macOS)*

Beim ersten Start meldet macOS möglicherweise:

> „start.command" kann nicht geöffnet werden, da es von einem nicht verifizierten
> Entwickler stammt. macOS kann nicht überprüfen, ob diese App frei von Schadsoftware ist.

Das ist normal bei allem, was nicht aus dem App Store kommt. macOS markiert jede heruntergeladene Datei automatisch, unabhängig vom Inhalt.

Im Terminal aus Schritt 2 einmalig ausführen:

```
xattr -dr com.apple.quarantine .
```

Der Punkt am Ende gehört dazu — er steht für den aktuellen Ordner. Danach lässt sich alles normal starten.

Wem das nicht geheuer ist: Der gesamte Quelltext liegt offen in diesem Repository. Bei einem Programm, das dauerhaft das Mikrofon abhört und Tastendrücke sendet, ist Misstrauen angebracht — lies den Code vorher, er ist kurz.

**3. Kürzel in Capture One anlegen**

`Bearbeiten` → `Tastaturkürzel bearbeiten`

- Das Standard-Set **duplizieren** (das Original lässt sich nicht ändern)
- **Wichtig:** Oben im Auswahlmenü auf dein neues Set umschalten. Wird das vergessen, passiert später nichts.
- Die Befehle **„Aufnahme"** (Kategorie *Kamera*) und **Kamera-Autofokus starten/stoppen** suchen. Am schnellsten geht das über das Suchfeld oben im Dialog.
- Diese Kürzel vergeben:

| Befehl | macOS | Windows |
|---|---|---|
| Aufnahme | Option + Shift + A | Strg + Alt + Shift + A |
| Kamera-Autofokus starten/stoppen | Option + Shift + F | Strg + Alt + Shift + F |

Unter Windows kommt Strg hinzu, weil Alt + Shift dort allein die Tastaturbelegung umschaltet.

Zum Prüfen: Beide Kürzel einmal von Hand drücken. Stellt die Kamera nicht scharf oder löst nicht aus, stimmt etwas an dieser Stelle nicht — dann hilft auch das Skript nicht weiter.

**4. Starten**

*Unter macOS:* Doppelklick auf **`start.command`**. Beim ersten Start fragt macOS zweimal nach Berechtigungen:

- **Mikrofon** — erlauben
- **Bedienungshilfen** — erlauben, danach das Terminal schließen und `start.command` erneut starten

*Unter Windows:* Doppelklick auf **`start.bat`**. Kommen die Tastendrücke nicht bei Capture One an, Rechtsklick → **Als Administrator ausführen** — Windows schränkt ein, welche Programme anderen Tastendrücke schicken dürfen.

Das Fenster muss geöffnet bleiben, solange du den Sprachauslöser benutzt. Beenden mit `Strg + C` oder durch Schließen des Fensters.

---

## Benutzung

Capture One in den Vordergrund holen, dann sprechen:

| Sagen | Was passiert | Ton |
|---|---|---|
| **„Capture One focus"** | Kamera stellt scharf | kurzes Ticken |
| **„Capture One take a photo"** oder **„Capture One shoot"** | Kamera löst aus | heller Klang |

Ein tiefer Ton meldet einen Fehler. Im Fenster erscheint zusätzlich, was erkannt wurde.

Fokus und Auslösen gehen direkt nacheinander — „focus" sagen, die Kamera kurz arbeiten lassen, dann „take a photo". Jeder Befehl sperrt nur sich selbst für einen Moment. So kann ein Echo nicht zweimal dasselbe auslösen, blockiert aber nie den anderen Befehl.

Die Phrasen sind bewusst mehrteilig. Ein einzelnes Wort würde im Gespräch ständig fehlauslösen.

---

## Auf Deutsch umstellen

Zwei Handgriffe.

**1. Deutsches Modell holen**

```
MODEL=vosk-model-small-de-0.15 bash setup.sh
```

Danach den englischen Modellordner `vosk-model-small-en-us-0.15` löschen, sonst liegen zwei nebeneinander.

**2. Phrasen ändern**

Oben in `voice_trigger.py` innerhalb von `COMMANDS` die `phrases`-Zeilen anpassen:

```python
COMMANDS = {
    "focus": {
        "phrases": ["capture one fokus"],
        ...
    },
    "capture": {
        "phrases": ["capture one auslösen", "capture one foto"],
        ...
    },
}
```

Alles andere in `COMMANDS` so lassen.

Nur Kleinbuchstaben, keine Satzzeichen, zwei Wörter oder mehr.

Jedes Wort muss im Wortschatz des Modells vorkommen. Unbekannte Wörter werden stillschweigend übersprungen — das sieht dann genauso aus, als würde das Mikrofon nicht funktionieren. Zum Prüfen:

```
./venv/bin/python voice_trigger.py --verbose
```

Das zeigt alles, was erkannt wird, samt Warnungen über fehlende Wörter.

Sonst ist nichts anzupassen. Tastenkürzel, Audio und die Capture-One-Seite sind sprachunabhängig.

---

## Wenn etwas nicht klappt

**„Von einem nicht verifizierten Entwickler"**
Siehe Schritt 2a. Im Terminal `xattr -dr com.apple.quarantine .` im Projektordner ausführen.

**„Es hört mich, aber es passiert nichts"**
Das Kürzel kommt nicht an. Drück Option + Shift + A (bzw. Option + Shift + F für den Fokus) von Hand in Capture One. Passiert dabei nichts, ist entweder das duplizierte Set nicht ausgewählt oder keine Kamera verbunden.

**„Auslösen klappt, Fokus tut nichts"**
Nicht jede Kamera unterstützt Autofokus über die Tethering-Verbindung. Öffne in Capture One das Werkzeug *Kamerafokus*: Ist dort der AF-Knopf ausgegraut, bieten Kamera oder Objektiv das nicht an. Prüf außerdem, ob das Objektiv selbst auf AF steht.

**„osascript is not allowed to send keystrokes"**
Die Bedienungshilfen fehlen. Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen → Terminal aktivieren. Terminal danach komplett beenden (Cmd + Q) und neu starten, sonst greift die Änderung nicht.

**„Es hört mich gar nicht"**
Falsches Mikrofon. Im Terminal sehen, welche es gibt:

```
./venv/bin/python voice_trigger.py --devices
```

Dann in `voice_trigger.py` die Zeile `INPUT_DEVICE = None` auf die gewünschte Nummer ändern.

**Anderes Tastenkürzel gewünscht**
In `voice_trigger.py` innerhalb von `COMMANDS` beim jeweiligen Befehl `mac_key` und `mac_modifiers` anpassen. Mögliche Modifikatoren: `command down`, `option down`, `shift down`, `control down`.

---

## Wie es funktioniert

Das Skript hört durchgehend am Mikrofon mit und vergleicht das Gehörte mit einer kurzen, festen Wortliste. Bei einem Treffer sendet es das passende Tastenkürzel an Capture One — genau so, als hättest du es selbst gedrückt. Capture One merkt keinen Unterschied.

Die Spracherkennung übernimmt [Vosk](https://alphacephei.com/vosk/). Weil nur zwischen einer Handvoll fester Phrasen unterschieden werden muss, ist die Trefferquote auch bei Umgebungsgeräuschen hoch und die Verzögerung liegt unter einer Sekunde.

---

## Grenzen

- **Windows ist ungetestet.** Code und Installation sind vorhanden und sollten funktionieren, aber noch niemand hat sie mit einer echten Kamera ausprobiert. Wer es versucht, möge bitte in jedem Fall ein Issue aufmachen — das ist im Moment das Wichtigste für dieses Projekt.
- **Capture One muss im Vordergrund sein.** Das Skript holt es selbst nach vorn, bei mehreren Fenstern kann es aber das falsche erwischen.
- **Vosk ist auf 0.3.44 festgelegt.** Ab 0.3.45 gibt es keine macOS-Pakete mehr. Nicht erhöhen.
- **Python 3.10 mindestens.** Für 3.9 gibt es kein `cffi`-Paket für Intel-Macs — und 3.9 ist genau das, was macOS mitbringt.

---

## Was es nicht ist

Kein Sprachassistent. Es versteht zwei Anweisungen — scharfstellen und auslösen — und sonst nichts. Das ist Absicht: Ein Sprachmodell dazwischen würde mehrere Sekunden kosten, eine Bestätigung verlangen und gelegentlich etwas anderes tun als gewünscht. Für einen Auslöser ist das untauglich.

Wer Capture One weitergehend steuern will — Varianten, Ebenen, Ausgabe —, findet das bei [capture-one-mcp](https://glama.ai/mcp/servers/byjustinjones/capture-one-mcp). Tethered Capture ist dort ausdrücklich nicht enthalten, insofern ergänzen sich beide.

---

## Lizenz

MIT

---

## Danksagung

Die Spracherkennung übernimmt [Vosk](https://alphacephei.com/vosk/), Apache 2.0.
Das englische Modell `vosk-model-small-en-us-0.15` steht ebenfalls unter Apache 2.0.
Wer ein anderes einsetzt, sollte in die Lizenzspalte der
[Modellliste](https://alphacephei.com/vosk/models) schauen — nicht alle sind frei
verwendbar.

## Rechtlicher Hinweis

Dieses Projekt steht in keiner Verbindung zu Capture One A/S und wird von dort weder
unterstützt noch empfohlen. „Capture One" ist eine Marke des Unternehmens und wird
hier nur verwendet, um zu beschreiben, womit dieses Werkzeug arbeitet.

Es handelt sich um ein eigenständiges Programm. Es enthält keinen Capture-One-Code
und verändert nichts innerhalb der Anwendung — es sendet ein Tastenkürzel, genau wie
es ein Fußschalter oder ein Makropad täte.
