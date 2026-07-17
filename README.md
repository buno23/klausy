<div align="center">
  <img src="Webseite/klausy-logo.jpeg" alt="Klausy Logo" width="80" style="border-radius:12px">
  <h1>🧠 Klausy – KI-Assistent mit 80+ Tools</h1>
  <p><strong>Entwickelt im Kurs „Artificial Intelligence Agency"</strong><br>
  der <a href="https://www.humboldt-auf-scharfenberg.de/">JuniorAkademie Berlin „Humboldt auf Scharfenberg"</a></p>

  <p>
    <a href="https://klausy.onrender.com" target="_blank">
      <img src="https://img.shields.io/badge/Live-Demo-c96020?style=for-the-badge&logo=render" alt="Live Demo">
    </a>
    <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask" alt="Flask">
  </p>
</div>

---

## ✨ Über Klausy

**Klausy** ist ein KI-Assistent mit **über 80 Tools**, der während der **JuniorAkademie Berlin** im Kurs *"Artificial Intelligence Agency"* auf der Insel Scharfenberg entwickelt wurde.

Statt nur zu chatten, kann Klausy **autonom handeln** – er sucht das Web, checkt das Wetter, übersetzt Texte, generiert QR-Codes, macht Preisvergleiche, beantwortet Quizfragen und vieles mehr – alles über einfache **TOOL:-Befehle**.

---

## 🚀 Live-Demo

👉 **[https://klausy.onrender.com](https://klausy.onrender.com)**

---

## 🛠️ Features

| Kategorie | Tools |
|---|---|
| ⭐ **Recherche** | `DEEPRESEARCH`, `SEARCH`, `NEWS`, `WIKI`, `DEFINE`, `DICTIONARY` |
| 🌤️ **Wetter & Zeit** | `WEATHER`, `TIME`, `DATE`, `TIMESTAMP`, `MATH` |
| 🌐 **Web & Netzwerk** | `BROWSE`, `URLINFO`, `EXTRACTLINKS`, `PING`, `IPINFO`, `MYIP`, `SHORTEN`, `QRCODE` |
| 💻 **Entwicklung** | `GITHUB`, `FORMATJSON`, `HASH`, `BASE64`, `BIN`, `ASCII`, `UNITS`, `WORDCOUNT` |
| 💰 **Finanzen** | `PRICE`, `CURRENCY` |
| 🌍 **Geo & Welt** | `COUNTRY`, `EARTHQUAKE`, `ISS`, `UNIVERSITY`, `SPACEFLIGHT` |
| 🎮 **Spiele & Quiz** | `TRIVIA`, `NUMBERS`, `DICEROLL` |
| 🎭 **Unterhaltung** | `INSPIRE`, `ADVICE`, `DOG`, `CAT`, `LYRICS`, `TRANSLATE` |
| 🔧 **Werkzeuge** | `PASSWORD`, `UUID`, `RANDOM`, `RECIPE` |

---

## 📋 Technologie-Stack

| Technologie | Verwendung |
|---|---|
| **Python 3.11+** | Backend & API-Logik |
| **Flask** | Web-Server & REST-API |
| **OpenAI / GPUStack** | KI-Sprachmodell (LLM) |
| **HTML5 / CSS3 / JavaScript** | Frontend (Chat-UI) |
| **Discord.py** | Discord-Bot-Integration |
| **Render** | Hosting & Deployment |

---

## 🏗️ Projektstruktur

```
📁 klausy/
├── agent.py                  # Haupt-Agent mit KI-Logik & 80+ Tools
├── gui.py                    # Desktop-GUI (optional)
├── requirements.txt          # Python-Abhängigkeiten
├── .env.example              # Vorlage für Umgebungsvariablen
├── .gitignore                # Git-Ignore-Regeln
├── Webseite/
│   ├── web_api.py            # Flask-Backend (Web-API + Auth)
│   ├── index.html            # Frontend (Webseite mit Chat)
│   ├── klausy-logo.jpeg      # Logo
│   └── start.bat             # Starter für Windows
└── Memorys/                  # Chat-Verläufe (lokal, ignoriert)
```

---

## 🔧 Lokale Installation

### Voraussetzungen

- Python 3.11 oder höher
- API-Key für ein LLM (z. B. OpenAI oder GPUStack)

### Setup

```bash
# Repository klonen
git clone https://github.com/buno23/klausy.git
cd klausy

# .env-Datei anlegen
cp .env.example .env
# -> Dort deinen API-Key eintragen

# Abhängigkeiten installieren
pip install -r requirements.txt

# Web-Server starten
cd Webseite
python web_api.py
```

👉 **Im Browser öffnen:** [http://localhost:5000](http://localhost:5000)

---

## 🚢 Deployment auf Render

1. Repository auf GitHub pushen
2. Auf [render.com](https://render.com) → **New Web Service**
3. Repo verbinden, **Start Command:**
   ```
   cd Webseite && python web_api.py
   ```
4. **Environment Variables** setzen:
   - `OPENAI_API_KEY` = dein API-Key
   - `WEB_PASSWORD` = (optional) Passwort für den Zugriff
   - `DISCORD_TOKEN` = (optional) Discord-Bot-Token

---

## 📝 Verwendung

Einfach eine Frage im Chat stellen – Klausy entscheidet selbst, ob ein Tool nötig ist:

```
User:  Wie ist das Wetter in Berlin?
Klausy: 🌤️ Aktuell 22°C, bewölkt...

User:  TOOL: DEEPRESEARCH Quantencomputer
Klausy: 🔍 [Ergebnisse aus Web + Wikipedia...]
```

Oder **gezielt** mit `TOOL:`:
- `TOOL: WEATHER Berlin`
- `TOOL: SEARCH Python Tutorials`
- `TOOL: QRCODE Hallo Welt`
- `TOOL: ADVICE`
