# -*- coding: utf-8 -*-
"""Klausy Bot - Web-API (Flask-Server)
Start: python web_api.py
Dann: http://localhost:5000
"""

import os, sys, json, threading, datetime, uuid, re, hashlib
from flask import Flask, request, jsonify, send_from_directory, Response, make_response
from flask_cors import CORS

# Projekt-Pfade
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Agent importieren (initialisiert OpenAI-Client)
from agent import process_message, TOOL_HELP_TEXT, parse_tool_shortcut, run_tool_command, handle_tool_command

# Flask-App
app = Flask(__name__, static_folder=SCRIPT_DIR, static_url_path="")
CORS(app)

# Sessions: {session_id: {"history": [...], "memory": "", "settings": {}}}
sessions = {}
sessions_lock = threading.Lock()

MAX_SESSIONS = 100


def get_or_create_session(session_id):
    with sessions_lock:
        if session_id not in sessions:
            sessions[session_id] = {
                "history": [],
                "memory": "",
                "created": datetime.datetime.now().isoformat(),
                "settings": {}
            }
            if len(sessions) > MAX_SESSIONS:
                oldest = sorted(sessions.keys(), key=lambda k: sessions[k].get("created", ""))
                for old_id in oldest[:len(sessions) - MAX_SESSIONS]:
                    del sessions[old_id]
        return sessions[session_id]


def parse_tools_from_help():
    """Parse tools from TOOL_HELP_TEXT into structured data."""
    tools = []
    current_category = "Allgemein"
    icon_map = {
        "SEHR NÜTZLICH": "fas fa-star",
        "WEB & NETZWERK": "fas fa-network-wired",
        "ENTWICKLUNG": "fas fa-code",
        "FINANZEN": "fas fa-coins",
        "GEO & WELT": "fas fa-globe-americas",
        "WISSEN & QUIZ": "fas fa-puzzle-piece",
        "UNTERHALTUNG": "fas fa-mask",
        "LIFESTYLE": "fas fa-glass-martini-alt",
        "HILFSMITTEL": "fas fa-tools",
    }
    for line in TOOL_HELP_TEXT.split("\n"):
        line = line.strip()
        # Category header
        cat_match = re.match(r'^[⭐🌟🎯]{1,2}\s*(.+)$', line)
        if cat_match:
            current_category = cat_match.group(1).strip()
            continue
        # Tool line: NAME <param> - Description
        tool_match = re.match(r'^([A-Z][A-Z0-9_/-]+)\s+(.*?)(?:\s+-\s+(.*))?$', line)
        if not tool_match:
            tool_match = re.match(r'^([A-Z][A-Z0-9_/-]+)\s+(.+)$', line)
        if tool_match:
            name = tool_match.group(1).strip()
            rest = tool_match.group(2).strip()
            desc = ""
            if " - " in rest:
                parts = rest.split(" - ", 1)
                params = parts[0].strip()
                desc = parts[1].strip()
            else:
                params = rest
            tools.append({
                "name": name,
                "params": params,
                "description": desc,
                "category": current_category,
                "icon": icon_map.get(current_category.upper(), "fas fa-terminal")
            })
    return tools


ALL_TOOLS = parse_tools_from_help()

# ═══════════════════════════════════════════
# PASSWORDSCHUTZ (versteckt)
# ═══════════════════════════════════════════
PASSWORD_FILE = os.path.join(SCRIPT_DIR, ".webpass")
AUTH_COOKIE = "klausy_auth"

def load_password():
    """Lese Passwort aus .webpass-Datei (erstes Zeichen = Hash-Modus)."""
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if raw.startswith("hash:"):
                return raw[5:], "hash"  # gespeicherter Hash
            return raw, "plain"
    return None, None

def check_password(input_pw):
    stored, mode = load_password()
    # Fallback: WEB_PASSWORD als Environment-Variable
    if not stored:
        stored = os.environ.get("WEB_PASSWORD")
    if not stored:
        return True  # kein Passwort gesetzt = frei
    if mode == "hash":
        return hashlib.sha256(input_pw.encode()).hexdigest() == stored
    return input_pw == stored

PASSWORD_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Klausy</title>
<style>
body{margin:0;background:#0d0d0d;color:#d4d4d4;font-family:Inter,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}
.w{text-align:center;max-width:320px}
.w img{height:48px;opacity:.7;margin-bottom:16px}
.w p{font-size:.8rem;color:#888;margin-bottom:20px}
.w input{width:100%;padding:10px 14px;background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;color:#d4d4d4;font-size:.85rem;outline:none;font-family:Inter,sans-serif;box-sizing:border-box;transition:border-color .3s}
.w input:focus{border-color:#c96020}
.w .h{font-size:.65rem;color:#555;margin-top:10px;cursor:default;user-select:none}
.w .e{color:#c44;font-size:.72rem;margin-top:8px;display:none}
</style>
</head>
<body>
<div class="w">
<img src="klausy-logo.jpeg" alt="">
<p>Zugang geschützt</p>
<input type="password" id="pw" placeholder="" autofocus onkeydown="if(event.key==='Enter')login()">
<div class="e" id="err">Falsches Passwort</div>
<div class="h">&middot;</div>
</div>
<script>
function login(){
  fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pw:document.getElementById('pw').value})})
  .then(r=>r.json()).then(d=>{if(d.ok)location.reload();else document.getElementById('err').style.display='block'})
  .catch(()=>document.getElementById('err').style.display='block');
}
window.addEventListener('load',function(){setTimeout(function(){document.getElementById('pw').focus()},100)});
</script>
</body>
</html>"""

@app.before_request
def check_auth():
    """Prüfe Authentifizierung vor jeder Anfrage – KEINE Ausnahmen."""
    stored, _ = load_password()
    # Fallback: WEB_PASSWORD als Environment-Variable
    if not stored:
        stored = os.environ.get("WEB_PASSWORD")
    if not stored:
        return None  # kein Passwort gesetzt = frei zugänglich
    # Login-Endpunkt immer erlauben
    if request.path == "/api/auth":
        return None
    # Cookie prüfen
    token = request.cookies.get(AUTH_COOKIE)
    if token and check_password(token):
        return None
    # API-Aufrufe (außer Login) → 401
    if request.path.startswith("/api/"):
        return jsonify({"error": "Nicht autorisiert. Bitte zuerst einloggen."}), 401
    # Alles andere → Login-Seite (auch /index.html, /klausy-logo.jpeg, etc.)
    resp = make_response(PASSWORD_HTML)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


# ═══════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════

@app.route("/api/auth", methods=["POST"])
def auth():
    """Passwortprüfung. Bei Erfolg Cookie setzen."""
    data = request.get_json(silent=True) or {}
    pw = data.get("pw", "")
    if check_password(pw):
        resp = jsonify({"ok": True})
        resp.set_cookie(AUTH_COOKIE, pw, max_age=None, httponly=True, samesite="Lax")
        return resp
    return jsonify({"ok": False})

@app.route("/")
def index():
    return send_from_directory(SCRIPT_DIR, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()
    session_id = data.get("session_id") or request.headers.get("X-Session-Id", "default")

    if not user_input:
        return jsonify({"error": "Keine Nachricht übermittelt."}), 400

    try:
        # Direkte Tool-Befehle erkennen und sofort ausführen
        shortcut_cmd, shortcut_arg = parse_tool_shortcut(user_input)
        if shortcut_cmd:
            tool_output = run_tool_command(shortcut_cmd, shortcut_arg)
            session = get_or_create_session(session_id)
            session["history"].append(f"User: {user_input}")
            session["history"].append(f"Assistant: {tool_output}")
            return jsonify({
                "answer": tool_output,
                "session_id": session_id,
                "message_count": len(session["history"]),
            })

        session = get_or_create_session(session_id)
        history = list(session["history"])
        memory = session["memory"]

        answer, new_memory, updated_history = process_message(
            user_input, history, memory, save=False
        )

        session["history"] = updated_history
        session["memory"] = new_memory

        # Extract tool names used in the answer
        tools_used = re.findall(r'\[(\w+)\]', answer)
        tools_used = list(dict.fromkeys(tools_used))[:5]

        return jsonify({
            "answer": answer,
            "session_id": session_id,
            "memory": new_memory[:200] if new_memory else "",
            "tools_used": tools_used,
            "message_count": len(updated_history),
        })

    except Exception as e:
        return jsonify({"error": f"Server-Fehler: {str(e)}"}), 500


@app.route("/api/tools", methods=["GET"])
def get_tools():
    """Return all available tools."""
    category = request.args.get("category", "")
    search = request.args.get("search", "").lower()
    tools = ALL_TOOLS
    if category:
        tools = [t for t in tools if t["category"].lower() == category.lower()]
    if search:
        tools = [t for t in tools if search in t["name"].lower() or search in t["description"].lower()]
    return jsonify({
        "tools": tools,
        "count": len(tools),
        "categories": list(dict.fromkeys(t["category"] for t in ALL_TOOLS))
    })


@app.route("/api/tools/categories", methods=["GET"])
def get_tool_categories():
    """Return all tool categories."""
    cats = []
    seen = set()
    for t in ALL_TOOLS:
        if t["category"] not in seen:
            seen.add(t["category"])
            cats.append({
                "name": t["category"],
                "icon": t["icon"],
                "count": sum(1 for x in ALL_TOOLS if x["category"] == t["category"])
            })
    return jsonify({"categories": cats})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming chat response (Server-Sent Events)."""
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()
    session_id = data.get("session_id") or request.headers.get("X-Session-Id", "default")

    if not user_input:
        return jsonify({"error": "Keine Nachricht übermittelt."}), 400

    def generate():
        try:
            session = get_or_create_session(session_id)
            history = list(session["history"])
            memory = session["memory"]

            answer, new_memory, updated_history = process_message(
                user_input, history, memory, save=False
            )

            session["history"] = updated_history
            session["memory"] = new_memory

            # Stream the answer character by character for live effect
            chunk_size = 3
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            tools_used = re.findall(r'\[(\w+)\]', answer)
            tools_used = list(dict.fromkeys(tools_used))[:5]
            yield f"data: {json.dumps({'type': 'done', 'tools_used': tools_used, 'message_count': len(updated_history)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/reset", methods=["POST"])
def reset_session():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or request.headers.get("X-Session-Id", "default")
    with sessions_lock:
        sessions[session_id] = {
            "history": [], "memory": "",
            "created": datetime.datetime.now().isoformat(), "settings": {}
        }
    return jsonify({"status": "ok", "session_id": session_id})


@app.route("/api/session", methods=["GET"])
def get_session_info():
    session_id = request.headers.get("X-Session-Id", "default")
    session = get_or_create_session(session_id)
    return jsonify({
        "session_id": session_id,
        "message_count": len(session["history"]),
        "has_memory": bool(session["memory"]),
        "created": session.get("created", ""),
    })


@app.route("/api/session/settings", methods=["GET", "POST"])
def session_settings():
    session_id = request.headers.get("X-Session-Id", "default")
    session = get_or_create_session(session_id)
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        session["settings"].update(data)
        return jsonify({"status": "ok", "settings": session["settings"]})
    return jsonify({"settings": session.get("settings", {})})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "bot": "Klausy Bot",
        "version": "2.0",
        "tools_count": len(ALL_TOOLS),
        "active_sessions": len(sessions),
    })


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(SCRIPT_DIR, filename)


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║   🚀  Klausy Bot Web-API 2.0    ║")
    print(f"  ╠══════════════════════════════════╣")
    print(f"  ║  🌐  http://localhost:{port}          ║")
    print(f"  ║  📡  {len(ALL_TOOLS)} Tools geladen            ║")
    print(f"  ║  📝  Strg+C zum Beenden          ║")
    print(f"  ╚══════════════════════════════════╝\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
