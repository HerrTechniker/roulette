#!/usr/bin/env python3
import json
import os
import random
import hashlib
import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Tuple

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

BET_TYPES = {
    "Straight": {"payout": 35, "inside": True, "selection_count": 1},
    "Split": {"payout": 17, "inside": True, "selection_count": 2},
    "Street": {"payout": 11, "inside": True, "selection_count": 3},
    "Corner": {"payout": 8, "inside": True, "selection_count": 4},
    "Six Line": {"payout": 5, "inside": True, "selection_count": 6},
    "Red/Black": {"payout": 1, "inside": False, "selection_count": None},
    "Gerade/Ungerade": {"payout": 1, "inside": False, "selection_count": None},
    "1-18/19-36": {"payout": 1, "inside": False, "selection_count": None},
    "Dutzend": {"payout": 2, "inside": False, "selection_count": None},
    "Kolonne": {"payout": 2, "inside": False, "selection_count": None},
}

THEMES = {
    "light": {
        "bg": "#f7f7fb",
        "panel": "#ffffff",
        "text": "#1b1b1b",
        "accent": "#1565c0",
        "canvas": "#ffffff",
        "wheel": "#1b5e20",
    },
    "dark": {
        "bg": "#1e1f26",
        "panel": "#2b2d3a",
        "text": "#f5f5f5",
        "accent": "#90caf9",
        "canvas": "#262834",
        "wheel": "#0f3d1d",
    },
    "system": {},
}


@dataclass
class Bet:
    bet_type: str
    amount: float
    selection: List[str]
    payout_ratio: int
    is_inside: bool


def ensure_data_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(
                {
                    "default_start_balance": 100.0,
                    "admin_users": ["admin"],
                    "ui_theme": "system",
                },
                config_file,
                indent=2,
            )

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


def validate_bet_amount(amount: float, is_inside: bool) -> bool:
    if amount not in ALLOWED_BETS:
        return False
    if is_inside and amount < MIN_INSIDE_BET:
        return False
    if not is_inside and amount < MIN_OUTSIDE_BET:
        return False
    return True


def selection_from_outside(bet_type: str, selection: str) -> Optional[List[str]]:
    if bet_type == "Red/Black":
        if selection == "red":
            return [str(n) for n in RED_NUMBERS]
        if selection == "black":
            return [str(n) for n in BLACK_NUMBERS]
        return None
    if bet_type == "Gerade/Ungerade":
        if selection == "gerade":
            return [str(n) for n in range(2, 37, 2)]
        if selection == "ungerade":
            return [str(n) for n in range(1, 37, 2)]
        return None
    if bet_type == "1-18/19-36":
        if selection == "1-18":
            return [str(n) for n in range(1, 19)]
        if selection == "19-36":
            return [str(n) for n in range(19, 37)]
        return None
    if bet_type == "Dutzend":
        if selection == "1-12":
            return [str(n) for n in range(1, 13)]
        if selection == "13-24":
            return [str(n) for n in range(13, 25)]
        if selection == "25-36":
            return [str(n) for n in range(25, 37)]
        return None
    if bet_type == "Kolonne":
        if selection == "1":
            return [str(n) for n in range(1, 37, 3)]
        if selection == "2":
            return [str(n) for n in range(2, 37, 3)]
        if selection == "3":
            return [str(n) for n in range(3, 37, 3)]
        return None
    return None


def resolve_bets(bets: List[Bet], result: str) -> Tuple[float, List[str]]:
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


class RouletteApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("American Roulette")
        self.geometry("980x720")
        self.resizable(False, False)

        ensure_data_files()
        self.users = load_json(USERS_FILE)
        self.config = load_json(CONFIG_FILE)
        if "ui_theme" not in self.config:
            self.config["ui_theme"] = "system"
            save_json(CONFIG_FILE, self.config)
        self.system_palette = {
            "bg": self.cget("bg"),
            "panel": self.cget("bg"),
            "text": "black",
            "accent": "#1565c0",
            "canvas": "white",
            "wheel": "#1b5e20",
        }
        self.current_user: Optional[str] = None
        self.current_bets: List[Bet] = []
        self.result_number: Optional[str] = None
        self.theme_var = tk.StringVar(value=self.config.get("ui_theme", "system"))

        self.frames: Dict[str, tk.Frame] = {}
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        for frame_class in (LoginFrame, RegisterFrame, AdminFrame, GameFrame, OverviewFrame):
            frame = frame_class(parent=container, app=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[frame_class.__name__] = frame

        self.show_frame("LoginFrame")
        self.apply_theme(self.theme_var.get())

    def show_frame(self, name: str) -> None:
        frame = self.frames[name]
        frame.tkraise()

    def refresh_users(self) -> None:
        self.users = load_json(USERS_FILE)

    def refresh_config(self) -> None:
        self.config = load_json(CONFIG_FILE)

    def save_users(self) -> None:
        save_json(USERS_FILE, self.users)

    def save_config(self) -> None:
        save_json(CONFIG_FILE, self.config)

    def add_theme_selector(self, parent: tk.Widget) -> None:
        bar = tk.Frame(parent)
        bar.pack(fill="x", pady=5)
        tk.Label(bar, text="Design:").pack(side="left", padx=5)
        selector = ttk.Combobox(
            bar,
            values=["system", "light", "dark"],
            textvariable=self.theme_var,
            state="readonly",
            width=10,
        )
        selector.pack(side="left")
        selector.bind("<<ComboboxSelected>>", lambda _event: self.on_theme_change())

    def on_theme_change(self) -> None:
        new_theme = self.theme_var.get()
        self.config["ui_theme"] = new_theme
        self.save_config()
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name: str) -> None:
        if theme_name == "system":
            palette = self.system_palette
        else:
            palette = THEMES[theme_name]
        self.configure(bg=palette["bg"])
        style = ttk.Style(self)
        style.configure("TLabel", background=palette["bg"], foreground=palette["text"])
        style.configure("TFrame", background=palette["bg"])
        style.configure("TButton", background=palette["panel"], foreground=palette["text"])
        style.configure("TCombobox", fieldbackground=palette["panel"], foreground=palette["text"])
        for frame in self.frames.values():
            self.update_widget_colors(frame, palette)
            if isinstance(frame, GameFrame):
                frame.update_theme(palette)

    def update_widget_colors(self, widget: tk.Widget, palette: dict) -> None:
        if isinstance(widget, ttk.Widget):
            for child in widget.winfo_children():
                self.update_widget_colors(child, palette)
            return
        if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Toplevel)):
            widget.configure(bg=palette["bg"])
        elif isinstance(widget, tk.Label):
            widget.configure(bg=palette["bg"], fg=palette["text"])
        elif isinstance(widget, tk.Button):
            widget.configure(bg=palette["panel"], fg=palette["text"], activebackground=palette["accent"])
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=palette["panel"], fg=palette["text"], insertbackground=palette["text"])
        elif isinstance(widget, tk.Listbox):
            widget.configure(bg=palette["panel"], fg=palette["text"])
        elif isinstance(widget, tk.Text):
            widget.configure(bg=palette["panel"], fg=palette["text"], insertbackground=palette["text"])
        elif isinstance(widget, tk.Canvas):
            widget.configure(bg=palette["canvas"])
        for child in widget.winfo_children():
            self.update_widget_colors(child, palette)


class LoginFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, app: RouletteApp) -> None:
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="American Roulette", font=("Helvetica", 20, "bold")).pack(pady=20)
        app.add_theme_selector(self)

        form = tk.Frame(self)
        form.pack(pady=10)
        tk.Label(form, text="Benutzername").grid(row=0, column=0, sticky="e")
        tk.Label(form, text="Passwort").grid(row=1, column=0, sticky="e")
        self.username_entry = tk.Entry(form, width=30)
        self.password_entry = tk.Entry(form, show="*", width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        btn_row = tk.Frame(self)
        btn_row.pack(pady=15)
        tk.Button(btn_row, text="Einloggen", width=15, command=self.login).grid(row=0, column=0, padx=5)
        tk.Button(btn_row, text="Registrieren", width=15, command=lambda: app.show_frame("RegisterFrame")).grid(
            row=0, column=1, padx=5
        )
        tk.Button(btn_row, text="Admin", width=15, command=self.admin_login).grid(row=0, column=2, padx=5)
        tk.Button(btn_row, text="Gewinnübersicht", width=15, command=lambda: app.show_frame("OverviewFrame")).grid(
            row=0, column=3, padx=5
        )

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        user = self.app.users.get(username)
        if not user or user.get("password_hash") != hash_password(password):
            messagebox.showerror("Login fehlgeschlagen", "Benutzername oder Passwort falsch.")
            return
        self.app.current_user = username
        self.app.frames["GameFrame"].refresh()
        self.app.show_frame("GameFrame")

    def admin_login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        user = self.app.users.get(username)
        if not user or user.get("password_hash") != hash_password(password):
            messagebox.showerror("Login fehlgeschlagen", "Benutzername oder Passwort falsch.")
            return
        if username not in self.app.config.get("admin_users", []):
            messagebox.showerror("Keine Berechtigung", "Kein Admin-Recht.")
            return
        self.app.current_user = username
        self.app.frames["AdminFrame"].refresh()
        self.app.show_frame("AdminFrame")


class RegisterFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, app: RouletteApp) -> None:
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="Registrieren", font=("Helvetica", 18, "bold")).pack(pady=20)
        app.add_theme_selector(self)

        form = tk.Frame(self)
        form.pack(pady=10)
        tk.Label(form, text="Benutzername").grid(row=0, column=0, sticky="e")
        tk.Label(form, text="Passwort").grid(row=1, column=0, sticky="e")
        self.username_entry = tk.Entry(form, width=30)
        self.password_entry = tk.Entry(form, show="*", width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        btn_row = tk.Frame(self)
        btn_row.pack(pady=15)
        tk.Button(btn_row, text="Registrieren", width=15, command=self.register).grid(row=0, column=0, padx=5)
        tk.Button(btn_row, text="Zurück", width=15, command=lambda: app.show_frame("LoginFrame")).grid(
            row=0, column=1, padx=5
        )

    def register(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Fehler", "Bitte Benutzername und Passwort eingeben.")
            return
        if username in self.app.users:
            messagebox.showerror("Fehler", "Benutzername existiert bereits.")
            return
        start_balance = self.app.config.get("default_start_balance", 100.0)
        self.app.users[username] = {"password_hash": hash_password(password), "balance": start_balance}
        self.app.save_users()
        messagebox.showinfo("Registrierung", f"Registrierung abgeschlossen. Startkapital: {start_balance:.2f}€")
        self.app.refresh_users()
        self.app.show_frame("LoginFrame")


class AdminFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, app: RouletteApp) -> None:
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="Admin-Bereich", font=("Helvetica", 18, "bold")).pack(pady=20)
        app.add_theme_selector(self)
        self.balance_var = tk.StringVar()

        form = tk.Frame(self)
        form.pack(pady=10)
        tk.Label(form, text="Startkapital (€)").grid(row=0, column=0, sticky="e")
        self.balance_entry = tk.Entry(form, textvariable=self.balance_var, width=20)
        self.balance_entry.grid(row=0, column=1, padx=10, pady=5)

        btn_row = tk.Frame(self)
        btn_row.pack(pady=15)
        tk.Button(btn_row, text="Speichern", width=15, command=self.save_balance).grid(row=0, column=0, padx=5)
        tk.Button(btn_row, text="Zurück", width=15, command=self.back).grid(row=0, column=1, padx=5)

    def refresh(self) -> None:
        self.balance_var.set(f"{self.app.config.get('default_start_balance', 100.0):.2f}")

    def save_balance(self) -> None:
        raw = self.balance_var.get().replace(",", ".")
        try:
            amount = float(raw)
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiger Betrag.")
            return
        if amount <= 0:
            messagebox.showerror("Fehler", "Betrag muss größer 0 sein.")
            return
        self.app.config["default_start_balance"] = round(amount, 2)
        self.app.save_config()
        messagebox.showinfo("Gespeichert", f"Startkapital aktualisiert: {amount:.2f}€")

    def back(self) -> None:
        self.app.refresh_config()
        self.app.show_frame("LoginFrame")


class OverviewFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, app: RouletteApp) -> None:
        super().__init__(parent)
        self.app = app
        tk.Label(self, text="Gewinnübersicht & Feld-Erklärung", font=("Helvetica", 16, "bold")).pack(pady=15)
        app.add_theme_selector(self)
        text = (
            "Innenfelder (min 0,50€)\n"
            "- Straight (eine Zahl, inkl. 0/00): Auszahlung 35:1\n"
            "- Split (zwei Zahlen): Auszahlung 17:1\n"
            "- Street (drei Zahlen in einer Reihe): Auszahlung 11:1\n"
            "- Corner (vier Zahlen im Block): Auszahlung 8:1\n"
            "- Six Line (sechs Zahlen, zwei Reihen): Auszahlung 5:1\n\n"
            "Außenfelder (min 5€)\n"
            "- Red/Black: Auszahlung 1:1\n"
            "- Gerade/Ungerade: Auszahlung 1:1\n"
            "- 1-18/19-36: Auszahlung 1:1\n"
            "- Dutzend (1-12, 13-24, 25-36): Auszahlung 2:1\n"
            "- Kolonne (1, 2, 3): Auszahlung 2:1\n\n"
            "American Roulette enthält 0 und 00."
        )
        label = tk.Label(self, text=text, justify="left")
        label.pack(padx=20, pady=10)

        tk.Button(self, text="Zurück", width=15, command=lambda: app.show_frame("LoginFrame")).pack(pady=10)


class GameFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, app: RouletteApp) -> None:
        super().__init__(parent)
        self.app = app
        self.spin_running = False
        self.spin_index = 0
        self.spin_speed_ms = 70
        self.remaining_spin_steps = 0
        self.wheel_color = THEMES["light"]["wheel"]
        self.canvas_color = THEMES["light"]["canvas"]

        header = tk.Frame(self)
        header.pack(fill="x", pady=10)
        self.balance_var = tk.StringVar()
        self.user_var = tk.StringVar()
        tk.Label(header, textvariable=self.user_var, font=("Helvetica", 14, "bold")).pack(side="left", padx=10)
        tk.Label(header, textvariable=self.balance_var, font=("Helvetica", 14)).pack(side="left", padx=10)
        tk.Button(header, text="Logout", command=self.logout).pack(side="right", padx=10)
        self.app.add_theme_selector(header)

        main = tk.Frame(self)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main)
        left.pack(side="left", fill="y", padx=20)
        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=20)

        tk.Label(left, text="Wette platzieren", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.bet_type_var = tk.StringVar(value="Straight")
        self.amount_var = tk.DoubleVar(value=ALLOWED_BETS[0])
        self.selection_var = tk.StringVar()

        tk.Label(left, text="Wettart").pack(anchor="w")
        ttk.Combobox(left, values=list(BET_TYPES.keys()), textvariable=self.bet_type_var, state="readonly").pack(
            fill="x", pady=5
        )
        tk.Label(left, text="Auswahl (Zahl(en) oder Text)").pack(anchor="w")
        tk.Entry(left, textvariable=self.selection_var).pack(fill="x", pady=5)
        tk.Label(left, text="Einsatz (€)").pack(anchor="w")
        ttk.Combobox(left, values=[str(bet) for bet in ALLOWED_BETS], textvariable=self.amount_var, state="readonly").pack(
            fill="x", pady=5
        )
        tk.Button(left, text="Wette hinzufügen", command=self.add_bet).pack(fill="x", pady=5)
        tk.Button(left, text="Gewinnübersicht", command=lambda: app.show_frame("OverviewFrame")).pack(
            fill="x", pady=5
        )

        tk.Label(left, text="Aktuelle Wetten").pack(anchor="w", pady=(10, 0))
        self.bet_list = tk.Listbox(left, width=35, height=10)
        self.bet_list.pack(fill="y", pady=5)
        tk.Button(left, text="Letzte Wette entfernen", command=self.remove_last_bet).pack(fill="x")

        wheel_frame = tk.Frame(right)
        wheel_frame.pack(pady=10)
        tk.Label(wheel_frame, text="Rouletterad", font=("Helvetica", 14, "bold")).pack()
        self.wheel_canvas = tk.Canvas(wheel_frame, width=380, height=380, bg=self.canvas_color, highlightthickness=1)
        self.wheel_canvas.pack(pady=10)
        self.number_label = tk.Label(wheel_frame, text="Aktuelles Feld: -", font=("Helvetica", 14))
        self.number_label.pack(pady=5)
        tk.Button(wheel_frame, text="Drehen", command=self.start_spin).pack(pady=5)

        result_frame = tk.Frame(right)
        result_frame.pack(fill="both", expand=True, pady=10)
        tk.Label(result_frame, text="Ergebnisse", font=("Helvetica", 14, "bold")).pack(anchor="w")
        self.result_text = tk.Text(result_frame, height=10, state="disabled")
        self.result_text.pack(fill="both", expand=True)

        self.draw_wheel()

    def refresh(self) -> None:
        username = self.app.current_user or ""
        balance = self.app.users.get(username, {}).get("balance", 0.0)
        self.user_var.set(f"Spieler: {username}")
        self.balance_var.set(f"Kontostand: {balance:.2f}€")
        self.bet_list.delete(0, tk.END)
        self.app.current_bets = []
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.configure(state="disabled")
        self.number_label.config(text="Aktuelles Feld: -")

    def logout(self) -> None:
        self.app.current_user = None
        self.app.refresh_users()
        self.app.show_frame("LoginFrame")

    def add_bet(self) -> None:
        bet_type = self.bet_type_var.get()
        selection_raw = self.selection_var.get().strip()
        try:
            amount = float(str(self.amount_var.get()).replace(",", "."))
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiger Betrag.")
            return

        meta = BET_TYPES[bet_type]
        is_inside = meta["inside"]
        if not validate_bet_amount(amount, is_inside):
            if is_inside:
                messagebox.showerror("Fehler", "Innenfeld min 0,50€, erlaubte Einsätze: 0,50/1/2/5/10/25.")
            else:
                messagebox.showerror("Fehler", "Außenfeld min 5€, erlaubte Einsätze: 5/10/25.")
            return

        if is_inside:
            selections = [item.strip() for item in selection_raw.split(",") if item.strip()]
            needed = meta["selection_count"]
            if len(selections) != needed or any(item not in WHEEL for item in selections):
                messagebox.showerror("Fehler", "Ungültige Auswahl für diese Wettart.")
                return
        else:
            if not selection_raw:
                messagebox.showerror("Fehler", "Bitte eine Auswahl eingeben.")
                return
            selections = selection_from_outside(bet_type, selection_raw.lower())
            if selections is None:
                messagebox.showerror("Fehler", "Ungültige Auswahl für diese Wettart.")
                return

        username = self.app.current_user or ""
        balance = self.app.users.get(username, {}).get("balance", 0.0)
        if balance < amount:
            messagebox.showerror("Fehler", "Nicht genügend Guthaben.")
            return

        bet = Bet(
            bet_type=bet_type,
            amount=amount,
            selection=selections,
            payout_ratio=meta["payout"],
            is_inside=is_inside,
        )
        self.app.current_bets.append(bet)
        self.bet_list.insert(tk.END, f"{bet_type}: {amount:.2f}€ -> {', '.join(selections)}")
        self.selection_var.set("")

    def remove_last_bet(self) -> None:
        if not self.app.current_bets:
            return
        self.app.current_bets.pop()
        self.bet_list.delete(tk.END)

    def start_spin(self) -> None:
        if self.spin_running:
            return
        if not self.app.current_bets:
            messagebox.showinfo("Hinweis", "Bitte zuerst Wetten platzieren.")
            return
        self.spin_running = True
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.configure(state="disabled")
        self.remaining_spin_steps = random.randint(45, 70)
        self.spin_speed_ms = 70
        self.animate_spin()

    def animate_spin(self) -> None:
        if self.remaining_spin_steps <= 0:
            self.finish_spin()
            return
        self.spin_index = (self.spin_index + 1) % len(WHEEL)
        current_number = WHEEL[self.spin_index]
        self.highlight_number(current_number)
        self.remaining_spin_steps -= 1
        if self.remaining_spin_steps < 15:
            self.spin_speed_ms = min(200, self.spin_speed_ms + 15)
        self.after(self.spin_speed_ms, self.animate_spin)

    def finish_spin(self) -> None:
        self.spin_running = False
        result = WHEEL[self.spin_index]
        self.app.result_number = result
        self.number_label.config(text=f"Aktuelles Feld: {result}")
        self.resolve_and_display(result)

    def resolve_and_display(self, result: str) -> None:
        username = self.app.current_user or ""
        total_change, summaries = resolve_bets(self.app.current_bets, result)
        self.app.users[username]["balance"] = round(self.app.users[username]["balance"] + total_change, 2)
        self.app.save_users()
        self.app.refresh_users()
        self.refresh()

        self.result_text.configure(state="normal")
        self.result_text.insert(tk.END, f"Kugel fällt auf: {result}\n\n")
        for summary in summaries:
            self.result_text.insert(tk.END, f"{summary}\n")
        self.result_text.configure(state="disabled")
        self.app.current_bets = []
        self.bet_list.delete(0, tk.END)

    def draw_wheel(self) -> None:
        self.wheel_canvas.delete("all")
        center = 190
        radius = 160
        self.wheel_canvas.create_oval(
            center - radius,
            center - radius,
            center + radius,
            center + radius,
            fill=self.wheel_color,
        )
        for idx, number in enumerate(WHEEL):
            angle = (360 / len(WHEEL)) * idx
            x = center + (radius - 20) * math.cos(math.radians(angle))
            y = center + (radius - 20) * math.sin(math.radians(angle))
            fill = "white"
            if number not in {"0", "00"}:
                value = int(number)
                if value in RED_NUMBERS:
                    fill = "red"
                elif value in BLACK_NUMBERS:
                    fill = "black"
            self.wheel_canvas.create_text(x, y, text=number, fill=fill, font=("Helvetica", 9, "bold"))
        self.highlight_marker = self.wheel_canvas.create_oval(
            center - 12, center - radius - 5, center + 12, center - radius + 19, fill="#fbc02d"
        )

    def highlight_number(self, number: str) -> None:
        center = 190
        radius = 160
        idx = WHEEL.index(number)
        angle = (360 / len(WHEEL)) * idx
        x = center + (radius - 20) * math.cos(math.radians(angle))
        y = center + (radius - 20) * math.sin(math.radians(angle))
        self.wheel_canvas.coords(self.highlight_marker, x - 12, y - 12, x + 12, y + 12)
        self.number_label.config(text=f"Aktuelles Feld: {number}")

    def update_theme(self, palette: dict) -> None:
        self.canvas_color = palette["canvas"]
        self.wheel_color = palette["wheel"]
        self.wheel_canvas.configure(bg=self.canvas_color)
        self.draw_wheel()


def main() -> None:
    app = RouletteApp()
    app.mainloop()


if __name__ == "__main__":
    main()
