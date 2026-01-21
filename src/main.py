#!/usr/bin/env python3
import getpass
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

ALLOWED_BETS = [0.5, 1.0, 2.0, 5.0, 10.0, 25.0]
MIN_INSIDE_BET = 0.5
MIN_OUTSIDE_BET = 5.0

RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36,
}
BLACK_NUMBERS = {
    2, 4, 6, 8, 10, 11, 13, 15, 17,
    20, 22, 24, 26, 28, 29, 31, 33, 35,
}

WHEEL = ["0", "00"] + [str(n) for n in range(1, 37)]


@dataclass
class Bet:
    bet_type: str
    amount: float
    selection: List[str]
    payout_ratio: int
    is_inside: bool


class RouletteGame:
    def __init__(self, users: Dict[str, dict], config: dict):
        self.users = users
        self.config = config

    def spin(self) -> str:
        return random.choice(WHEEL)

    def resolve_bets(self, bets: List[Bet], result: str) -> Tuple[float, List[str]]:
        total_change = 0.0
        summaries = []
        for bet in bets:
            if result in bet.selection:
                winnings = bet.amount * bet.payout_ratio
                total_change += winnings
                summaries.append(
                    f"Gewinn: {bet.bet_type} ({', '.join(bet.selection)}) +{winnings:.2f}€"
                )
            else:
                total_change -= bet.amount
                summaries.append(
                    f"Verlust: {bet.bet_type} ({', '.join(bet.selection)}) -{bet.amount:.2f}€"
                )
        return total_change, summaries


def ensure_data_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump({"default_start_balance": 100.0, "admin_users": ["admin"]}, config_file, indent=2)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as users_file:
            json.dump({}, users_file, indent=2)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(users: Dict[str, dict], config: dict) -> None:
    username = input("Benutzername: ").strip()
    if username in users:
        print("Benutzername existiert bereits.")
        return
    password = getpass.getpass("Passwort: ")
    start_balance = config.get("default_start_balance", 100.0)
    users[username] = {
        "password_hash": hash_password(password),
        "balance": start_balance,
    }
    save_json(USERS_FILE, users)
    print(f"Registrierung abgeschlossen. Startkapital: {start_balance:.2f}€")


def login_user(users: Dict[str, dict]) -> Optional[str]:
    username = input("Benutzername: ").strip()
    password = getpass.getpass("Passwort: ")
    user = users.get(username)
    if not user:
        print("Benutzername oder Passwort falsch.")
        return None
    if user.get("password_hash") != hash_password(password):
        print("Benutzername oder Passwort falsch.")
        return None
    print(f"Willkommen, {username}.")
    return username


def admin_menu(config: dict) -> None:
    while True:
        print("\nAdmin-Menü")
        print("1) Startkapital festlegen")
        print("2) Zurück")
        choice = input("Auswahl: ").strip()
        if choice == "1":
            try:
                amount = float(input("Neues Startkapital (€): ").replace(",", "."))
            except ValueError:
                print("Ungültiger Betrag.")
                continue
            if amount <= 0:
                print("Betrag muss größer 0 sein.")
                continue
            config["default_start_balance"] = round(amount, 2)
            save_json(CONFIG_FILE, config)
            print(f"Startkapital aktualisiert: {amount:.2f}€")
        elif choice == "2":
            return
        else:
            print("Ungültige Auswahl.")


def parse_amount(raw_amount: str) -> Optional[float]:
    try:
        amount = float(raw_amount.replace(",", "."))
    except ValueError:
        return None
    return amount


def validate_bet_amount(amount: float, is_inside: bool) -> bool:
    if amount not in ALLOWED_BETS:
        return False
    if is_inside and amount < MIN_INSIDE_BET:
        return False
    if not is_inside and amount < MIN_OUTSIDE_BET:
        return False
    return True


def create_bet(bet_type: str, amount: float, selection: List[str], payout_ratio: int, is_inside: bool) -> Bet:
    return Bet(bet_type=bet_type, amount=amount, selection=selection, payout_ratio=payout_ratio, is_inside=is_inside)


def choose_bet() -> Optional[Bet]:
    print("\nWettarten:")
    print("1) Straight (eine Zahl, inkl. 0/00)")
    print("2) Split (zwei Zahlen)")
    print("3) Street (drei Zahlen in einer Reihe)")
    print("4) Corner (vier Zahlen im Block)")
    print("5) Six Line (sechs Zahlen, zwei Reihen)")
    print("6) Red / Black")
    print("7) Gerade / Ungerade")
    print("8) 1-18 / 19-36")
    print("9) Dutzend (1-12 / 13-24 / 25-36)")
    print("10) Kolonne (1-34, 2-35, 3-36)")
    print("0) Fertig")

    choice = input("Auswahl: ").strip()
    if choice == "0":
        return None

    amount = parse_amount(input("Einsatz (€): "))
    if amount is None:
        print("Ungültiger Betrag.")
        return None

    if choice == "1":
        selection = input("Zahl (0, 00, 1-36): ").strip()
        if selection not in WHEEL:
            print("Ungültige Zahl.")
            return None
        if not validate_bet_amount(amount, True):
            print("Ungültiger Einsatz. Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            return None
        return create_bet("Straight", amount, [selection], 35, True)

    if choice == "2":
        raw = input("Zwei Zahlen, z.B. 14,15: ").split(",")
        selection = [item.strip() for item in raw if item.strip()]
        if len(selection) != 2 or any(item not in WHEEL for item in selection):
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, True):
            print("Ungültiger Einsatz. Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            return None
        return create_bet("Split", amount, selection, 17, True)

    if choice == "3":
        raw = input("Drei Zahlen, z.B. 1,2,3: ").split(",")
        selection = [item.strip() for item in raw if item.strip()]
        if len(selection) != 3 or any(item not in WHEEL for item in selection):
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, True):
            print("Ungültiger Einsatz. Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            return None
        return create_bet("Street", amount, selection, 11, True)

    if choice == "4":
        raw = input("Vier Zahlen, z.B. 8,9,11,12: ").split(",")
        selection = [item.strip() for item in raw if item.strip()]
        if len(selection) != 4 or any(item not in WHEEL for item in selection):
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, True):
            print("Ungültiger Einsatz. Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            return None
        return create_bet("Corner", amount, selection, 8, True)

    if choice == "5":
        raw = input("Sechs Zahlen, z.B. 1,2,3,4,5,6: ").split(",")
        selection = [item.strip() for item in raw if item.strip()]
        if len(selection) != 6 or any(item not in WHEEL for item in selection):
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, True):
            print("Ungültiger Einsatz. Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            return None
        return create_bet("Six Line", amount, selection, 5, True)

    if choice == "6":
        selection = input("red oder black: ").strip().lower()
        if selection not in {"red", "black"}:
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, False):
            print("Ungültiger Einsatz. Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return None
        numbers = [str(n) for n in (RED_NUMBERS if selection == "red" else BLACK_NUMBERS)]
        return create_bet("Red/Black", amount, numbers, 1, False)

    if choice == "7":
        selection = input("gerade oder ungerade: ").strip().lower()
        if selection not in {"gerade", "ungerade"}:
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, False):
            print("Ungültiger Einsatz. Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return None
        if selection == "gerade":
            numbers = [str(n) for n in range(2, 37, 2)]
        else:
            numbers = [str(n) for n in range(1, 37, 2)]
        return create_bet("Gerade/Ungerade", amount, numbers, 1, False)

    if choice == "8":
        selection = input("1-18 oder 19-36: ").strip()
        if selection not in {"1-18", "19-36"}:
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, False):
            print("Ungültiger Einsatz. Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return None
        if selection == "1-18":
            numbers = [str(n) for n in range(1, 19)]
        else:
            numbers = [str(n) for n in range(19, 37)]
        return create_bet("1-18/19-36", amount, numbers, 1, False)

    if choice == "9":
        selection = input("1-12, 13-24 oder 25-36: ").strip()
        if selection not in {"1-12", "13-24", "25-36"}:
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, False):
            print("Ungültiger Einsatz. Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return None
        if selection == "1-12":
            numbers = [str(n) for n in range(1, 13)]
        elif selection == "13-24":
            numbers = [str(n) for n in range(13, 25)]
        else:
            numbers = [str(n) for n in range(25, 37)]
        return create_bet("Dutzend", amount, numbers, 2, False)

    if choice == "10":
        selection = input("Kolonne 1, 2 oder 3: ").strip()
        if selection not in {"1", "2", "3"}:
            print("Ungültige Auswahl.")
            return None
        if not validate_bet_amount(amount, False):
            print("Ungültiger Einsatz. Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return None
        if selection == "1":
            numbers = [str(n) for n in range(1, 37, 3)]
        elif selection == "2":
            numbers = [str(n) for n in range(2, 37, 3)]
        else:
            numbers = [str(n) for n in range(3, 37, 3)]
        return create_bet("Kolonne", amount, numbers, 2, False)

    print("Ungültige Auswahl.")
    return None


def show_payout_overview() -> None:
    print("\nGewinnübersicht & Feld-Erklärung")
    print("Innenfelder (min 0,50€):")
    print("- Straight (eine Zahl, inkl. 0/00): Auszahlung 35:1")
    print("- Split (zwei Zahlen): Auszahlung 17:1")
    print("- Street (drei Zahlen in einer Reihe): Auszahlung 11:1")
    print("- Corner (vier Zahlen im Block): Auszahlung 8:1")
    print("- Six Line (sechs Zahlen, zwei Reihen): Auszahlung 5:1")
    print("\nAußenfelder (min 5€):")
    print("- Red/Black: Auszahlung 1:1")
    print("- Gerade/Ungerade: Auszahlung 1:1")
    print("- 1-18/19-36: Auszahlung 1:1")
    print("- Dutzend (1-12, 13-24, 25-36): Auszahlung 2:1")
    print("- Kolonne (1, 2, 3): Auszahlung 2:1")
    print("\nAmerican Roulette enthält 0 und 00.")


def player_session(username: str, users: Dict[str, dict], config: dict) -> None:
    while True:
        print("\nSpieler-Menü")
        print("1) Spielen")
        print("2) Kontostand anzeigen")
        print("3) Gewinnübersicht")
        print("4) Logout")
        choice = input("Auswahl: ").strip()

        if choice == "1":
            bets: List[Bet] = []
            while True:
                bet = choose_bet()
                if bet is None:
                    break
                if users[username]["balance"] < bet.amount:
                    print("Nicht genügend Guthaben.")
                    continue
                bets.append(bet)
                print(f"Wette hinzugefügt: {bet.bet_type} {bet.amount:.2f}€")

            if not bets:
                print("Keine Wetten platziert.")
                continue

            result = RouletteGame(users, config).spin()
            print(f"\nDie Kugel fällt auf: {result}")
            total_change, summaries = RouletteGame(users, config).resolve_bets(bets, result)
            for summary in summaries:
                print(summary)

            users[username]["balance"] = round(users[username]["balance"] + total_change, 2)
            save_json(USERS_FILE, users)
            print(f"Neuer Kontostand: {users[username]['balance']:.2f}€")

        elif choice == "2":
            print(f"Kontostand: {users[username]['balance']:.2f}€")
        elif choice == "3":
            show_payout_overview()
        elif choice == "4":
            return
        else:
            print("Ungültige Auswahl.")


def main() -> None:
    ensure_data_files()
    users = load_json(USERS_FILE)
    config = load_json(CONFIG_FILE)

    while True:
        print("\nAmerican Roulette")
        print("1) Registrieren")
        print("2) Einloggen")
        print("3) Admin-Login")
        print("4) Gewinnübersicht")
        print("0) Beenden")

        choice = input("Auswahl: ").strip()
        if choice == "1":
            register_user(users, config)
            users = load_json(USERS_FILE)
        elif choice == "2":
            username = login_user(users)
            if username:
                player_session(username, users, config)
                users = load_json(USERS_FILE)
        elif choice == "3":
            username = login_user(users)
            if not username:
                continue
            if username not in config.get("admin_users", []):
                print("Kein Admin-Recht.")
                continue
            admin_menu(config)
            config = load_json(CONFIG_FILE)
        elif choice == "4":
            show_payout_overview()
        elif choice == "0":
            print("Auf Wiedersehen!")
            return
        else:
            print("Ungültige Auswahl.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
        sys.exit(0)
