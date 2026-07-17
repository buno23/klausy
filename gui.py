# -*- coding: utf-8 -*-
"""Klausy - Chat + Discord. Schön, simpel, fertig."""

import os, sys, threading, datetime
from dotenv import load_dotenv

# .env laden (Environment-Variablen aus Datei)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    import customtkinter as ctk
except ImportError:
    import subprocess as _sp
    _sp.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk


_ag = None
def ag():
    global _ag
    if _ag is None:
        from agent import process_message
        _ag = {"pm": process_message}
    return _ag


# ── Farben ──
C = {
    "bg":"#0d1117","panel":"#151b23","card":"#161b22","input":"#0d1117",
    "hover":"#1c2333","accent":"#2f81f7","text":"#e6edf3","sec":"#8b949e",
    "dim":"#484f58","msg_u":"#1c2333","msg_a":"#0d1117","border":"#21262d",
    "err":"#f85149","ok":"#3fb950","warn":"#d29922",
}


# ═══════════════════════════════════════════
# UI
# ═══════════════════════════════════════════
root = ctk.CTk()
ctk.set_appearance_mode("dark")
root.title("Klausy")
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"900x680+{(sw-900)//2}+{(sh-680)//2}")
root.minsize(600, 400)
root.configure(fg_color=C["bg"])

# ── State ──
chat_history = []
memory = ""
thinking = None
dc_running = False; dc_thread = None; dc_client = None
dc_token = os.getenv("DISCORD_TOKEN", ""); dc_trans = False


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════
def now():
    return datetime.datetime.now().strftime("%H:%M")

def scroll_down():
    root.after_idle(lambda: cf._parent_canvas.yview_moveto(1.0))

def status(text, typ="ok"):
    cm = {"ok": C["ok"], "warn": C["warn"], "err": C["err"]}
    sl.configure(text=text, text_color=cm.get(typ, C["sec"]))

def add_msg(role, text):
    bg = C["msg_u"] if role == "user" else C["msg_a"]
    pre = "Du" if role == "user" else "Klausy"
    fc = C["text"]
    pc = C["accent"]

    # Äußere Box mit schmalem Rand
    outer = ctk.CTkFrame(cf, fg_color="transparent")
    outer.pack(fill="x", padx=14, pady=(2, 0))

    # Farbbalken links (für KI-Nachrichten)
    if role == "ai" or role == "tool":
        bar = ctk.CTkFrame(outer, fg_color=C["accent"], width=3, corner_radius=2)
        bar.pack(side="left", fill="y", padx=(0, 10))

    b = ctk.CTkFrame(outer, fg_color=bg, corner_radius=10)
    b.pack(side="left", fill="x", expand=True)

    h = ctk.CTkFrame(b, fg_color="transparent")
    h.pack(fill="x", padx=16, pady=(10, 0))
    ctk.CTkLabel(h, text=pre, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=pc).pack(side="left")
    ctk.CTkLabel(h, text=now(), font=ctk.CTkFont(size=9),
                 text_color=C["dim"]).pack(side="right")

    lbl = ctk.CTkLabel(b, text=text,
        font=ctk.CTkFont(family="Segoe UI", size=13),
        text_color=fc, wraplength=550, justify="left")
    lbl.pack(anchor="w", padx=16, pady=(8, 12))
    scroll_down()


def think_start():
    global thinking
    if thinking:
        try: thinking.destroy()
        except: pass
    thinking = ctk.CTkFrame(cf, fg_color=C["msg_a"], corner_radius=10)
    thinking.pack(fill="x", padx=12, pady=3)
    ctk.CTkLabel(thinking, text="Klausy", font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=C["accent"]).pack(anchor="w", padx=16, pady=(10, 0))
    ctk.CTkLabel(thinking, text="● ● ●", font=ctk.CTkFont(size=14),
                 text_color=C["dim"]).pack(anchor="w", padx=16, pady=(4, 12))
    scroll_down()

def think_stop():
    global thinking
    if thinking:
        try: thinking.destroy()
        except: pass
        thinking = None


# ═══════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════
def send():
    global chat_history, memory
    t = inp_box.get("1.0", "end-1c").strip()
    if not t: return
    inp_box.delete("1.0", "end")
    add_msg("user", t)
    status("Thinking...", "warn")

    try: a = ag()
    except Exception as e:
        add_msg("ai", f"API Error: {e}")
        status("Error", "err")
        return

    # Einfach an KI übergeben – sie erkennt selbst, ob ein Tool nötig ist
    threading.Thread(target=lambda: chat(t), daemon=True).start()

def chat(text):
    global memory
    root.after(0, think_start)
    try:
        ans, nm, uh = ag()["pm"](text, chat_history, memory, save=True)
        memory = nm
        chat_history.clear()
        chat_history.extend(uh)
        root.after(0, lambda: (think_stop(), add_msg("ai", ans), status("Ready")))
    except Exception as e:
        err_msg = str(e)
        root.after(0, lambda err=err_msg: (think_stop(), add_msg("ai", f"Error:\n{err}"), status("Error", "err")))


# ═══════════════════════════════════════════
# DISCORD
# ═══════════════════════════════════════════
def toggle_dc():
    if dc_trans: return
    if dc_running: stop_dc()
    else: start_dc()

def start_dc():
    global dc_running, dc_thread, dc_client, dc_trans
    tok = os.getenv("DISCORD_TOKEN")
    if not tok or dc_running or dc_trans: return
    dc_trans = True
    dc_ui("starting")
    status("Starting Discord...", "warn")
    def _r():
        global dc_running, dc_client, dc_trans
        try:
            from agent import create_discord_client
            cl = create_discord_client()
            dc_client = cl
            root.after(0, lambda: dc_ready(cl))
            cl.run(tok, log_handler=None)
        except Exception as e:
            root.after(0, lambda e=e: dc_err(str(e)))
        finally:
            if dc_running: root.after(0, dc_done)
    dc_thread = threading.Thread(target=_r, daemon=True)
    dc_thread.start()

def dc_ready(cl):
    global dc_running, dc_trans
    dc_running = True; dc_trans = False
    nm = getattr(cl.user, "name", "Bot")
    dc_ui("online", nm)
    status(f"Discord: {nm}")

def dc_err(msg):
    global dc_running, dc_trans, dc_client
    dc_running = False; dc_trans = False; dc_client = None
    dc_ui("error")

def dc_done():
    global dc_running, dc_trans, dc_client
    dc_running = False; dc_trans = False; dc_client = None
    dc_ui("offline")

def stop_dc():
    global dc_running, dc_client, dc_trans
    if not dc_running or not dc_client or dc_trans: return
    dc_trans = True
    dc_ui("stopping")
    status("Stopping Discord...", "warn")
    def _s():
        global dc_running, dc_client, dc_trans
        try:
            import asyncio
            asyncio.run_coroutine_threadsafe(dc_client.close(), dc_client.loop)
        except: pass
        root.after(0, dc_done)
        root.after(0, lambda: status("Discord stopped"))
    threading.Thread(target=_s, daemon=True).start()

def dc_ui(state, name=""):
    if state == "online":
        dc_dot.configure(text_color=C["ok"])
        dc_label.configure(text="Online", text_color=C["ok"])
        dc_bot.configure(text=f"🤖 {name}", text_color=C["ok"])
        dc_btn.configure(state="normal")
        update_btn_switch("on")
    elif state == "starting":
        dc_dot.configure(text_color=C["warn"])
        dc_label.configure(text="Starte...", text_color=C["warn"])
        dc_bot.configure(text="")
        dc_btn.configure(state="disabled")
        update_btn_switch("busy")
    elif state == "stopping":
        dc_dot.configure(text_color=C["warn"])
        dc_label.configure(text="Stoppe...", text_color=C["warn"])
        dc_btn.configure(state="disabled")
        update_btn_switch("busy")
    elif state == "error":
        dc_dot.configure(text_color=C["err"])
        dc_label.configure(text="Fehler", text_color=C["err"])
        dc_bot.configure(text="")
        dc_btn.configure(state="normal")
        update_btn_switch("err")
    else:
        dc_dot.configure(text_color=C["dim"])
        dc_label.configure(text="Offline", text_color=C["sec"])
        dc_bot.configure(text="")
        dc_btn.configure(state="normal")
        update_btn_switch("off")

def update_btn_switch(state="off"):
    if state == "on":
        dc_btn.configure(fg_color=C["ok"], hover_color="#2ea043", text="│  │")
    elif state == "off":
        dc_btn.configure(fg_color=C["dim"], hover_color="#58606e", text="○")
    elif state == "busy":
        dc_btn.configure(fg_color=C["warn"], hover_color="#bb8009", text="◐")
    elif state == "err":
        dc_btn.configure(fg_color=C["err"], hover_color="#da3633", text="✕")

def on_close():
    if dc_running and dc_client:
        try:
            import asyncio
            asyncio.run_coroutine_threadsafe(dc_client.close(), dc_client.loop)
        except: pass
    try:
        pr = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
        hf = os.path.join(pr, "Agent", "Memorys", "terminal_chat_history.txt")
        os.makedirs(os.path.dirname(hf), exist_ok=True)
        with open(hf, "w", encoding="utf-8") as f:
            f.write("\n".join(chat_history[-30:]) + "\n")
    except: pass
    root.destroy()


# ═══════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════

# Header
hdr = ctk.CTkFrame(root, fg_color=C["panel"], corner_radius=0, height=36)
hdr.pack(fill="x")
hdr.pack_propagate(False)

ctk.CTkLabel(hdr, text="Klausy", font=ctk.CTkFont(size=16, weight="bold"),
             text_color=C["accent"]).pack(side="left", padx=16)

# ── Main row: Chat + Discord Sidebar ──
main_row = ctk.CTkFrame(root, fg_color="transparent")
main_row.pack(fill="both", expand=True)

# ── Chat ──
chat_col = ctk.CTkFrame(main_row, fg_color=C["bg"])
chat_col.pack(side="left", fill="both", expand=True)

cf = ctk.CTkScrollableFrame(chat_col, fg_color=C["bg"], corner_radius=0,
    scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["dim"])
cf.pack(fill="both", expand=True, padx=0, pady=0)

add_msg("ai", "Hey, ich bin Klausy. Schreib mir einfach.")

# ── Discord Sidebar (rechts, breit) ──
side = ctk.CTkFrame(main_row, width=280, fg_color=C["panel"], corner_radius=0)
side.pack(side="right", fill="y")
side.pack_propagate(False)

ctk.CTkLabel(side, text="Discord Bot",
    font=ctk.CTkFont(size=14, weight="bold"),
    text_color=C["text"],
).pack(anchor="w", padx=20, pady=(22, 14))

# ── Discord Card ──
card = ctk.CTkFrame(side, fg_color=C["card"], corner_radius=14, border_width=1, border_color="#1e2533")
card.pack(fill="x", padx=14)

# Discord Icon + Header
icon_frame = ctk.CTkFrame(card, fg_color="transparent")
icon_frame.pack(anchor="center", pady=(22, 6))

# Discord-Logo-Icon (stilisierter Kreis)
dc_icon = ctk.CTkLabel(icon_frame, text="💬",
    font=ctk.CTkFont(size=34), text_color=C["accent"])
dc_icon.pack()

# Status-Pill (Badge)
badge_frame = ctk.CTkFrame(card, fg_color=C["card"], corner_radius=14)
badge_frame.pack(anchor="center", pady=(2, 0))

dc_dot = ctk.CTkLabel(badge_frame, text="●",
    font=ctk.CTkFont(size=14), text_color=C["dim"])
dc_dot.pack(side="left", padx=(16, 4), pady=(6, 6))

dc_label = ctk.CTkLabel(badge_frame, text="Offline",
    font=ctk.CTkFont(size=12, weight="bold"), text_color=C["sec"])
dc_label.pack(side="left", padx=(0, 16), pady=(6, 6))

# Bot-Name
dc_bot = ctk.CTkLabel(card, text="",
    font=ctk.CTkFont(size=11), text_color=C["ok"])
dc_bot.pack(anchor="center", pady=(4, 2))

# Trennlinie
ctk.CTkFrame(card, fg_color=C["border"], height=1).pack(fill="x", padx=20, pady=(14, 18))

# ── Toggle Switch ──
sw_frame = ctk.CTkFrame(card, fg_color="transparent")
sw_frame.pack(fill="x", padx=16, pady=(0, 22))

# Beschriftung links
sw_label = ctk.CTkLabel(sw_frame, text="Bot-Status",
    font=ctk.CTkFont(size=11), text_color=C["sec"])
sw_label.pack(side="left")

# Toggle-Button (stilisiert als Switch mit animiertem Kreis)
dc_btn = ctk.CTkButton(sw_frame, text="○",
    font=ctk.CTkFont(size=13, weight="bold"),
    fg_color=C["dim"], hover_color="#58606e",
    text_color="#fff", corner_radius=16, height=32, width=60,
    state="normal" if dc_token else "disabled",
    command=toggle_dc)
dc_btn.pack(side="right")

# Token-Hinweis (wenn kein Token)
if not dc_token:
    token_hint = ctk.CTkFrame(card, fg_color="#1c1f2b", corner_radius=8)
    token_hint.pack(fill="x", padx=16, pady=(0, 18))
    ctk.CTkLabel(token_hint,
        text="⚠ DISCORD_TOKEN nicht gesetzt",
        font=ctk.CTkFont(size=10), text_color=C["warn"],
    ).pack(padx=12, pady=8)

# Hilfetext unter dem Card
ctk.CTkLabel(side,
    text="Verwalte hier den Discord-Bot.\nDer Bot antwortet auf DMs.",
    font=ctk.CTkFont(size=10), text_color=C["dim"],
    justify="left",
).pack(anchor="w", padx=20, pady=(12, 0))

# ── Input ──
inp = ctk.CTkFrame(root, fg_color=C["panel"], corner_radius=0, height=56)
inp.pack(fill="x")
inp.pack_propagate(False)

ir = ctk.CTkFrame(inp, fg_color="transparent")
ir.pack(fill="x", padx=14, pady=(8, 4))

inp_box = ctk.CTkTextbox(ir, font=ctk.CTkFont(family="Cascadia Code", size=13),
    fg_color=C["input"], border_color=C["border"], border_width=1,
    corner_radius=8, height=34, wrap="word")
inp_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
inp_box.bind("<Return>", lambda e: (send(), "break") if not (e.state & 1) else None)

ctk.CTkButton(ir, text="Senden", font=ctk.CTkFont(size=12, weight="bold"),
    fg_color=C["accent"], hover_color="#388bfd",
    corner_radius=8, height=34, width=80, command=send).pack(side="right")

# ── Status Bar ──
sf = ctk.CTkFrame(root, fg_color=C["panel"], corner_radius=0, height=28)
sf.pack(side="bottom", fill="x")
sf.pack_propagate(False)

sl = ctk.CTkLabel(sf, text="Ready", font=ctk.CTkFont(size=10), text_color=C["ok"])
sl.pack(side="left", padx=12)

clk = ctk.CTkLabel(sf, text="", font=ctk.CTkFont(size=9), text_color=C["dim"])
clk.pack(side="right", padx=12)

def tick():
    clk.configure(text=now())
    root.after(1000, tick)
tick()


# ── Load ──
try:
    pr = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
    hf = os.path.join(pr, "Agent", "Memorys", "terminal_chat_history.txt")
    if os.path.exists(hf):
        with open(hf, "r", encoding="utf-8") as f:
            chat_history = [l.strip() for l in f if l.strip()]
except: pass

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
