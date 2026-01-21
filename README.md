# American Roulette (CLI)

Ein simples American-Roulette-Spiel (mit 0 und 00) in Python für JetBrains **PyCharm**.

## Features

- Login mit Benutzername + Passwort
- Admin kann das Startkapital für neue Spieler festlegen
- Erlaubte Einsätze: **0,50€**, **1€**, **2€**, **5€**, **10€**, **25€**
- Innenfelder (min. 0,50€) und Außenfelder (min. 5€)
- Gewinnübersicht mit Erklärung der Felder
- Persistente Speicherung in JSON (`data/`)

## Voraussetzungen (Requirements)

- Python 3.10+
- Standardbibliothek (keine externen Abhängigkeiten)

Siehe auch: `requirements.txt`.

## Installation & Start (PyCharm)

1. Projekt in PyCharm öffnen.
2. Python-Interpreter auswählen (3.10+).
3. `src/main.py` als Run-Konfiguration starten.

## Start (CLI)

```bash
python3 src/main.py
```

## Admin-Zugang

- Standard-Admin: Benutzername **admin**
- Legen Sie zuerst einen Benutzer `admin` über die Registrierung an.
- Danach kann dieser Benutzer über **Admin-Login** das Startkapital festlegen.

Die Standard-Konfiguration liegt in `data/config.json`:

```json
{
  "default_start_balance": 100.0,
  "admin_users": ["admin"]
}
```

## Gewinnübersicht & Feld-Erklärung

**Innenfelder (min 0,50€)**
- Straight (eine Zahl, inkl. 0/00): Auszahlung **35:1**
- Split (zwei Zahlen): Auszahlung **17:1**
- Street (drei Zahlen in einer Reihe): Auszahlung **11:1**
- Corner (vier Zahlen im Block): Auszahlung **8:1**
- Six Line (sechs Zahlen, zwei Reihen): Auszahlung **5:1**

**Außenfelder (min 5€)**
- Red/Black: Auszahlung **1:1**
- Gerade/Ungerade: Auszahlung **1:1**
- 1-18/19-36: Auszahlung **1:1**
- Dutzend (1-12, 13-24, 25-36): Auszahlung **2:1**
- Kolonne (1, 2, 3): Auszahlung **2:1**

**American Roulette** enthält die Zahlen **0** und **00**.
