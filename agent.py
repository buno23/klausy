import os, re, requests, secrets, json, uuid, random, datetime, sys, signal, math, hashlib, ast, threading, time
from html import unescape
from urllib.parse import quote, unquote, urlparse, urljoin
import asyncio
import discord
from openai import OpenAI
from dotenv import load_dotenv

# .env laden (Environment-Variablen aus Datei)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Projekt-Stammverzeichnis (einmal berechnet, überall genutzt)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def html_to_text(html):
    # Navigations- und Cookie-Hinweise entfernen
    html = re.sub(r"(?is)<(script|style|nav|footer|header).*?>.*?</\1>", "", html)
    # Cookie-Banner und Popups
    html = re.sub(r"(?is)<div[^>]*(cookie|banner|modal|overlay)[^>]*>.*?</div>", "", html)
    html = re.sub(r"(?is)<aside[^>]*>.*?</aside>", "", html)
    text = re.sub(r"<[^>]+>", "", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
    return text.strip()


TOOL_HELP_TEXT = """  Nutze: TOOL: NAME <param> (oder !tool NAME <param>)
  Hilfe: !help / !tools / TOOLS

  ⭐ SEHR NÜTZLICH
  DEEPRESEARCH <Q> - Tiefgreifende Recherche (Web+Wikipedia)
  SEARCH <Q> - Web-Suche
  WEATHER <Ort> - Wetter aktuell + Vorhersage (auch: morgen, Wochenende, 5 Tage)
  BROWSE <URL> - Webseite oeffnen & lesen
  NEWS <Q> - Aktuelle Nachrichten
  WIKI <Q> - Wikipedia-Artikel
  TRANSLATE <Text> - Uebersetzer (en->de: Text)
  DEFINE <Wort> - Wortdefinition
  DICTIONARY <Wort> - Englisches Woerterbuch
  MATH <expr> - Rechner (sin,cos,sqrt,log,pi)
  CALC <expr> - Rechner (einfach)
  TIME / DATE - Aktuelle Uhrzeit / Datum

  🌐 WEB & NETZWERK
  URLINFO <URL> - Seiten-Infos (Titel, Beschreibung)
  EXTRACTLINKS <URL> - Alle Links einer Seite
  PING <URL/Domain> - Erreichbarkeit pruefen
  IPINFO <IP> - IP-Informationen
  MYIP - Eigene oeffentliche IP
  SHORTEN <URL> - URL verkuerzen
  QRCODE <Text> - QR-Code generieren
  CURRENCY <B> <Q> <Z> - Waehrungsumrechner

  🔧 ENTWICKLUNG
  GITHUB <User> - GitHub-Profilinfo
  PYPISEARCH <Pkg> - PyPI-Paketinfo
  LYRICS <A - T> - Songtext (Artist - Title)
  FORMATJSON <JSON> - JSON formatieren
  WORDCOUNT <Text> - Woerter zaehlen
  BASE64 <enc/dec> <Text> - Base64 kodieren/dekodieren
  HASH <algo> <Text> - MD5/SHA256/SHA512
  BIN <Zahl> - Zahl in Bin/Hex/Oct
  ASCII <Text> - ASCII-Codes anzeigen
  UNITS <W> <E> <Z> - Einheiten umrechnen
  TIMESTAMP <ts> - Unix-Timestamp konvertieren

  💰 FINANZEN
  COINGECKO <Coin> - Crypto-Preis (z.B. bitcoin, ethereum)
  BITCOIN - Bitcoin Kurs (USD/EUR/GBP/JPY)
  PRICE <Produkt> - Preisvergleich (Web)

  🌍 GEO & WELT
  COUNTRY <Land> - Laenderinfos (Flagge, Hauptstadt, etc.)
  EARTHQUAKE - Aktuelle Erdbeben (M4.5+)
  ISS - ISS Position
  UNIVERSITY <Name> - Universitaetssuche
  SPACEFLIGHT - Aktuelle Space-Nachrichten

  🎯 WISSEN & QUIZ
  TRIVIA - Zufaellige Quizfrage
  RIDDLE - Zufaelliges Raetsel
  NUMBERS <Zahl> - Zahlen-Fakt
  DICEROLL <X> - Wuerfel (z.B. 3d6)

  🎉 UNTERHALTUNG
  JOKEAPI <Kat> - Witze (Any/Pun/Dark/Programming)
  DADJOKE - Papa-Witze
  CHUCKNORRIS - Chuck Norris Witze
  JOKE - Zufaelliger Witz
  KANYE - Kanye West Zitat
  INSPIRE - Inspirierendes Zitat
  QUOTE - Zufaelliges Zitat
  ADVICE - Zufaelliger Ratschlag
  EXCUSE - Zufaellige Ausrede
  BORED - Aktivitaetsvorschlag
  DOG - Zufaelliges Hundebild
  CAT - Zufaelliges Katzenbild
  FOX - Zufaelliges Fuchsbild
  POKEMON <Name> - Pokemon-Info
  SWAPI <Charakter> - Star Wars Charakter
  TVSHOW <Serie> - TV-Serien-Info
  GENDERIZE <Name> - Geschlecht aus Vornamen
  AGIFY <Name> - Alter aus Vornamen
  RANDOMUSER - Zufaelliger Fake-Benutzer
  USELESSFACT - Nutzloser Fakt
  CATFACT - Katzen-Fakt

  🍸 LIFESTYLE
  COCKTAIL <Name> - Cocktail-Rezept
  RECIPE <Q> - Rezept suchen
  REMIND <sec> <Text> - Erinnerung

  🛠 HILFSMITTEL
  LIST <Thema> - Infos sammeln & als Liste darstellen
  FILESEARCH <Q> - Dateien suchen
  SUMMARIZE <URL/Pfad> - Inhalt zusammenfassen
  MEMORY - Gespeicherte Erinnerungen anzeigen
  MEMORYTEST <Aktion> - Memory testen
  PASSWORD <L> - Passwort generieren
  UUID - Zufaellige UUID
  RANDOM <min> <max> - Zufallszahl
  CLICK <URL> <Nr> - Auf Webseite klicken
  FORMINFO <URL> - Formulare einer Seite
  SUBMITFORM <URL> <Nr> - Formular absenden
  META <URL> - Meta-Tags einer Seite
  PAGEWORDS <URL> - Wortanzahl einer Seite

  -- TOOLS / HELP - Diese Hilfe anzeigen"""

SYSTEM_PROMPT = f"""Du bist Klausy, ein faehiger KI-Assistent mit Tool-Zugriff. Dein Ziel: Anfragen korrekt, effizient und sicher loesen. Niemals Fakten erfinden.

- Name: Klausy. Stil: Wie ein erfahrener Engineer, nicht wie ein Chatbot.
- Sprache: Antworte IMMER auf Deutsch. Egal in welcher Sprache der Nutzer schreibt.
- Korrektheit > Geschwindigkeit. Wenn unsicher: zugeben, mit Tools verifizieren.
- Tools sind deine groesste Staerke. Nutze sie ohne Zoegern. Kombiniere sie.
- Fuer Recherche, Fakten, Wissen IMMER DEEPRESEARCH nutzen (nicht SEARCH). DEEPRESEARCH durchsucht Web + Wikipedia und vergleicht Quellen.
- SEARCH nur fuer sehr kurze/einfache Suchanfragen nutzen.
- IMMER das aktuelle Datum pruefen (TOOL: DATE) bevor du ueber Zeitdaten sprichst.
- Verifiziere Ergebnisse. Vertraue keinem Tool blind. Vergleiche Quellen.
- Halte Antworten kurz und praezise. Keine langen Ausführungen, kein ueberfluessiger Text.

TOOLS (nutze TOOL: NAME <param>):
{TOOL_HELP_TEXT}

ANTWORT-STIL: Kurz, direkt, klar, natuerlich. Listen bevorzugen. Keine ueberfluessigen Einleitungen. Keine uebermaessigen Emojis. Markdown zurueckhaltend.

CODE: Sauber, lesbar, sicher. Nur wenn angefragt. Kommentare nur fuer Intent.

MEMORY: Lies Memory vor JEDER Antwort. Speichere IMMER das aktuelle Datum mit. Speichere kompakt: Praeferenzen, Projekte, laufende Arbeit.

INTERN: Pruefen -> Planen -> Tools -> Verifizieren -> Antworten. Niemals zeigen.

QUALITAETS-CHECK: Ist das korrekt? Kann ein Tool es verbessern? Habe ich die Frage genau beantwortet?"""


def search_web(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get("https://html.duckduckgo.com/html/", params={"q": query, "kl": "de-de"}, headers=headers, timeout=15)
        resp.raise_for_status()
        text = html_to_text(resp.text)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:10]) or "Keine Ergebnisse gefunden."
    except Exception as e:
        return f"Fehler bei der Suche: {e}"


def safe_fetch(url, timeout=15, json_mode=False, headers=None):
    """Sichere HTTP-Anfrage mit Encoding-Erkennung."""
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        if resp.encoding and resp.encoding.lower() not in ("utf-8", "utf8"):
            resp.encoding = resp.apparent_encoding
        if json_mode:
            return resp.json()
        return resp.text
    except requests.exceptions.JSONDecodeError:
        return resp.text if not json_mode else {"error": "Ungültiges JSON"}
    except Exception as e:
        return f"Fehler: {e}" if not json_mode else {"error": str(e)}


def safe_fetch_json(url, timeout=15, headers=None):
    """Wie safe_fetch, aber gibt dict zurück."""
    return safe_fetch(url, timeout=timeout, json_mode=True, headers=headers)


def browse_url(url, timeout=8):
    if not urlparse(url).scheme:
        url = "http://" + url
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        if response.encoding and response.encoding.lower() != "utf-8":
            response.encoding = response.apparent_encoding
        return html_to_text(response.text)
    except Exception as e:
        return f"Fehler beim Öffnen der URL: {e}"


def normalize_url(url):
    if not urlparse(url).scheme:
        return "http://" + url
    return url


def fetch_html(url):
    url = normalize_url(url)
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        if response.encoding and response.encoding.lower() not in ("utf-8", "utf8"):
            response.encoding = response.apparent_encoding
        return response.text, response.url
    except Exception as e:
        raise RuntimeError(f"Fehler beim Abrufen der URL: {e}")


def get_page_info(url):
    try:
        html, final_url = fetch_html(url)
        title_match = re.search(r"(?is)<title>(.*?)</title>", html)
        title = title_match.group(1).strip() if title_match else "Kein Titel gefunden"
        desc_match = re.search(
            r'(?is)<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
            html,
        )
        if not desc_match:
            desc_match = re.search(
                r'(?is)<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']',
                html,
            )
        description = desc_match.group(1).strip() if desc_match else "Keine Beschreibung gefunden"
        return f"URL: {final_url}\nTitel: {title}\nBeschreibung: {description}"
    except Exception as e:
        return str(e)


def extract_links_from_url(url):
    try:
        html, _ = fetch_html(url)
        links = re.findall(r'(?is)<a\s+(?:[^>]*?\s)?href=["\'](.*?)["\']', html)
        filtered = []
        for link in links:
            if link.startswith("javascript:") or link.startswith("#"):
                continue
            if link not in filtered:
                filtered.append(link)
            if len(filtered) >= 20:
                break
        if not filtered:
            return "Keine Links auf der Seite gefunden."
        return "Links:" + "\n" + "\n".join(filtered)
    except Exception as e:
        return str(e)


def get_meta_tags(url):
    try:
        html, _ = fetch_html(url)
        meta_matches = re.findall(
            r'(?is)<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\']',
            html,
        )
        if not meta_matches:
            return "Keine Meta-Tags auf der Seite gefunden."
        lines = [f"{name}: {content}" for name, content in meta_matches[:20]]
        return "Meta-Tags:" + "\n" + "\n".join(lines)
    except Exception as e:
        return str(e)


def count_page_words(url):
    text = browse_url(url)
    if text.startswith("Fehler"):
        return text
    words = re.findall(r"\w+", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    snippet = "\n".join(lines[:5])
    return f"Wortanzahl: {len(words)}\n\nErster Text:\n{snippet}"


def parse_field_values(text):
    values = {}
    for match in re.findall(r'(\S+?)=("[^"]*"|\'[^\']*\'|\S+)', text):
        key = match[0]
        value = match[1].strip('"\'')
        values[key] = value
    return values


def split_first_word(text):
    if not text:
        return None, ""
    parts = text.strip().split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def extract_forms_from_url(url):
    try:
        html, final_url = fetch_html(url)
        forms = re.findall(r"(?is)<form\b(.*?)>(.*?)</form>", html)
        if not forms:
            return "Keine Formulare auf der Seite gefunden."
        output = []
        for idx, (attrs, body) in enumerate(forms, start=1):
            action = re.search(r'action=["\'](.*?)["\']', attrs, re.I)
            method = re.search(r'method=["\'](.*?)["\']', attrs, re.I)
            form_id = re.search(r'id=["\'](.*?)["\']', attrs, re.I)
            form_name = re.search(r'name=["\'](.*?)["\']', attrs, re.I)
            action_url = action.group(1) if action else final_url
            output.append(f"Formular {idx}: Methode={method.group(1).upper() if method else 'GET'} Aktion={action_url}")
            if form_id:
                output.append(f"  id={form_id.group(1)}")
            if form_name:
                output.append(f"  name={form_name.group(1)}")
            fields = []
            for input_tag in re.findall(r'(?is)<input\b(.*?)(?:/>|>)', body):
                name_match = re.search(r'name=["\'](.*?)["\']', input_tag, re.I)
                type_match = re.search(r'type=["\'](.*?)["\']', input_tag, re.I)
                value_match = re.search(r'value=["\'](.*?)["\']', input_tag, re.I)
                if name_match:
                    fields.append(
                        f"    {name_match.group(1)} ({type_match.group(1) if type_match else 'text'}) default={value_match.group(1) if value_match else ''}"
                    )
            for textarea_match in re.findall(r'(?is)<textarea\b(.*?)>(.*?)</textarea>', body):
                attrs_text, text_content = textarea_match
                name_match = re.search(r'name=["\'](.*?)["\']', attrs_text, re.I)
                if name_match:
                    default_value = text_content.strip().replace('\n', ' ')
                    fields.append(f"    {name_match.group(1)} (textarea) default={default_value}")
            if fields:
                output.extend(fields)
        return "\n".join(output)
    except Exception as e:
        return str(e)


def submit_form_on_url(argument):
    url, rest = split_first_word(argument)
    if not url:
        return "Bitte gib zuerst die URL und danach die Formularnummer und Felder an."
    form_number = 1
    values = {}
    if rest:
        next_token, remaining = split_first_word(rest)
        if next_token and next_token.isdigit():
            form_number = max(1, int(next_token))
            rest = remaining
        values = parse_field_values(rest)
    try:
        html, final_url = fetch_html(url)
        forms = re.findall(r"(?is)<form\b(.*?)>(.*?)</form>", html)
        if len(forms) < form_number:
            return f"Nur {len(forms)} Formular(e) gefunden. Bitte verwende eine gültige Formularnummer."
        attrs, body = forms[form_number - 1]
        action = re.search(r'action=["\'](.*?)["\']', attrs, re.I)
        method = re.search(r'method=["\'](.*?)["\']', attrs, re.I)
        action_url = urljoin(final_url, action.group(1)) if action else final_url
        method_name = method.group(1).upper() if method else "GET"
        data = values
        if method_name == "POST":
            response = requests.post(action_url, data=data, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        else:
            response = requests.get(action_url, params=data, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        content = html_to_text(response.text)
        return f"Formular gesendet an {response.url}\nStatus: {response.status_code}\nErste Ausgabe:\n{content[:1000]}"
    except Exception as e:
        return f"Fehler beim Absenden des Formulars: {e}"


def click_on_url(argument):
    """Klickt auf sichtbare interaktive Elemente (Links, Buttons, Submit-Inputs).
    
    Argument-Formate:
    - <URL>                          → zeigt alle klickbaren Elemente
    - <URL> <Text>                   → klickt erstes Element mit passendem Text oder href
    - <URL> <Nr>                     → klickt Element mit dieser Nummer
    - <URL> <Nr1,Nr2,Nr3>           → klickt mehrere Elemente (durch Komma getrennt)
    """
    url, query = split_first_word(argument)
    if not url:
        return "Bitte gib eine URL und optional Linktext/Nummer an."

    try:
        html, final_url = fetch_html(url)
    except Exception as e:
        return str(e)

    # Alle klickbaren Elemente sammeln
    clickable = []  # (type, tag, identifier, target_url)

    # <a href="..."> links
    for match in re.finditer(r'(?is)<a\s+(.*?)>(.*?)</a>', html):
        attrs = match.group(1)
        inner = match.group(2)
        href_match = re.search(r'href=["\'](.*?)["\']', attrs, re.I)
        if not href_match:
            continue
        href = href_match.group(1)
        if href.startswith("javascript:") or href.startswith("#"):
            continue
        text = html_to_text(inner).strip()
        identifier = text or href
        clickable.append(("link", "a", identifier, urljoin(final_url, href)))

    # <button> elements
    for match in re.finditer(r'(?is)<button\b(.*?)>(.*?)</button>', html):
        attrs = match.group(1)
        inner = match.group(2)
        onclick = re.search(r'onclick=["\'](.*?)["\']', attrs, re.I)
        form_action = re.search(r'formaction=["\'](.*?)["\']', attrs, re.I)
        text = html_to_text(inner).strip() or "Button"
        identifier = text
        target = form_action.group(1) if form_action else (onclick.group(1) if onclick else None)
        clickable.append(("button", "button", identifier, target))

    # <input type="submit"> and <input type="button">
    for match in re.finditer(r'(?is)<input\b(.*?)(?:/>|>)', html):
        attrs = match.group(1)
        inp_type = (re.search(r'type=["\'](.*?)["\']', attrs, re.I) or "").group(1) if re.search(r'type=["\'](.*?)["\']', attrs, re.I) else ""
        if inp_type.lower() not in ("submit", "button", "image"):
            continue
        value = (re.search(r'value=["\'](.*?)["\']', attrs, re.I) or "").group(1) if re.search(r'value=["\'](.*?)["\']', attrs, re.I) else inp_type
        form_action = re.search(r'formaction=["\'](.*?)["\']', attrs, re.I)
        target = form_action.group(1) if form_action else None
        clickable.append((f"input[{inp_type}]", "input", value, target))

    if not clickable:
        return "Keine klickbaren Elemente auf der Seite gefunden."

    # Kein Suchkriterium → Liste anzeigen
    if not query:
        lines = [f"Klickbare Elemente auf {final_url}:"]
        for idx, (typ, tag, ident, target) in enumerate(clickable, start=1):
            target_str = f" -> {target}" if target else ""
            lines.append(f"  {idx}. [{typ}] {ident[:60]}{target_str}")
        return "\n".join(lines)

    # Nach Nummer oder Text suchen
    query = query.strip()
    selection_lower = query.lower()

    # Mehrere Nummern (z.B. "1,3,5")
    if re.match(r'^[\d,\s]+$', query):
        nums = [int(n.strip()) for n in query.split(",") if n.strip().isdigit()]
        results = []
        for n in nums:
            if 1 <= n <= len(clickable):
                typ, tag, ident, target = clickable[n - 1]
                if target:
                    try:
                        t_html, t_url = fetch_html(target)
                        snippet = html_to_text(t_html)
                        results.append(f"#{n} [{typ}] {ident} -> {t_url}\n\n{snippet[:600]}")
                    except Exception as e:
                        results.append(f"#{n} [{typ}] {ident} -> Fehler: {e}")
                else:
                    results.append(f"#{n} [{typ}] {ident} (keine URL, JS-Event)")
            else:
                results.append(f"#{n} - ungültige Nummer (1-{len(clickable)})")
        return "\n\n---\n\n".join(results)

    # Einzelne Nummer
    if query.isdigit():
        n = int(query)
        if 1 <= n <= len(clickable):
            typ, tag, ident, target = clickable[n - 1]
            if target:
                try:
                    t_html, t_url = fetch_html(target)
                    snippet = html_to_text(t_html)
                    return f"#{n} [{typ}] {ident} -> {t_url}\n\n{snippet[:1000]}"
                except Exception as e:
                    return f"Fehler beim Öffnen: {e}"
            else:
                return f"#{n} [{typ}] {ident} (klickbar, aber kein direkter Link – JS-Event)"
        else:
            return f"Ungültige Nummer. Wähle 1-{len(clickable)}"

    # Text-Matching
    for idx, (typ, tag, ident, target) in enumerate(clickable, start=1):
        if selection_lower == ident.lower() or selection_lower in ident.lower():
            if target:
                try:
                    t_html, t_url = fetch_html(target)
                    snippet = html_to_text(t_html)
                    return f"[{typ}] {ident} -> {t_url}\n\n{snippet[:1000]}"
                except Exception as e:
                    return f"Fehler beim Öffnen: {e}"
            else:
                return f"[{typ}] {ident} (klickbar, aber kein direkter Link – JS-Event)"

    # Kein Treffer → Liste mit Hinweis
    lines = [f"Kein Treffer für '{query}'. Verfügbare Elemente:"]
    for idx, (typ, tag, ident, target) in enumerate(clickable, start=1):
        target_str = f" -> {target}" if target else ""
        lines.append(f"  {idx}. [{typ}] {ident[:60]}{target_str}")
    return "\n".join(lines)


def get_current_time(location=""):
    if not location:
        now = datetime.datetime.now()
        return f"Aktuelle Zeit: {now.strftime('%d.%m.%Y %H:%M:%S')}"
    try:
        url = f"https://worldtimeapi.org/api/timezone/{quote(location)}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            dt = data.get("datetime", "")
            tz = data.get("timezone", location)
            if dt:
                return f"Zeit in {tz}: {dt[:19].replace('T', ' ')}"
        return f"Zeit in {location}: {datetime.datetime.now().strftime('%H:%M:%S')} (geschätzt)"
    except Exception:
        return f"Zeit in {location}: {datetime.datetime.now().strftime('%H:%M:%S')} (geschätzt)"


def get_current_date():
    now = datetime.datetime.now()
    days_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    months_de = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
    wd = days_de[now.weekday()]
    m = months_de[now.month - 1]
    return f"Heute ist {wd}, der {now.day}. {m} {now.year}"


def roll_dice(arg):
    if not arg:
        return "Bitte gib Würfel an, z.B. 3d6 für 3x 6-seitige Würfel."
    match = re.match(r"(\d+)\s*d\s*(\d+)", arg.strip(), re.I)
    if not match:
        return f"Ungültiges Format: {arg}. Verwende z.B. 3d6"
    count = max(1, min(int(match.group(1)), 100))
    sides = max(2, min(int(match.group(2)), 1000))
    results = [random.randint(1, sides) for _ in range(count)]
    total = sum(results)
    return f"Würfel {count}d{sides}: {results} = {total}"


def generate_uuid():
    return f"UUID: {uuid.uuid4()}"


def base64_tool(argument):
    action, _, text = argument.strip().partition(" ")
    if not text:
        return "Bitte gib 'encode' oder 'decode' und den Text an."
    import base64
    try:
        if action.lower() in ("encode", "en"):
            encoded = base64.b64encode(text.encode()).decode()
            return f"Base64-kodiert: {encoded}"
        elif action.lower() in ("decode", "de"):
            decoded = base64.b64decode(text.encode()).decode()
            return f"Base64-dekodiert: {decoded}"
        else:
            return f"Unbekannte Aktion: {action}. Verwende 'encode' oder 'decode'."
    except Exception as e:
        return f"Fehler bei Base64: {e}"


def get_ip_info(ip=""):
    try:
        url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            lines = []
            for key, label in [("ip", "IP"), ("city", "Stadt"), ("region", "Region"), ("country_name", "Land"),
                               ("postal", "PLZ"), ("latitude", "Breite"), ("longitude", "Länge"),
                               ("org", "ISP"), ("timezone", "Zeitzone")]:
                if data.get(key):
                    lines.append(f"{label}: {data[key]}")
            return "\n".join(lines) if lines else "Keine IP-Info gefunden."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler bei IP-Abfrage: {e}"


def currency_convert(argument):
    parts = argument.strip().split()
    if len(parts) < 3:
        return "Bitte gib Betrag, Quellwährung und Zielwährung an, z.B. 100 EUR USD"
    try:
        amount = float(parts[0])
        src = parts[1].upper()
        dst = parts[2].upper()
        url = f"https://api.exchangerate-api.com/v4/latest/{src}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get("rates", {})
            if dst in rates:
                result = round(amount * rates[dst], 2)
                return f"{amount} {src} = {result} {dst}"
            return f"Zielwährung {dst} nicht gefunden."
        return f"Fehler: HTTP {resp.status_code}"
    except ValueError:
        return "Ungültiger Betrag."
    except Exception as e:
        return f"Fehler bei Währungsumrechnung: {e}"


def define_word(word):
    if not word:
        return "Bitte gib ein Wort an."
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/de/{quote(word)}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                word_name = entry.get("word", word)
                meanings = entry.get("meanings", [])
                lines = [f"Definition von '{word_name}':"]
                for m in meanings[:3]:
                    pos = m.get("partOfSpeech", "")
                    defs = m.get("definitions", [])
                    for d in defs[:2]:
                        definition = d.get("definition", "")
                        example = d.get("example", "")
                        line = f"  [{pos}] {definition}"
                        if example:
                            line += f"\n    Beispiel: {example}"
                        lines.append(line)
                return "\n".join(lines) if len(lines) > 1 else f"Keine Definitionen für '{word}' gefunden."
        return f"Keine Definition für '{word}' gefunden (Status: {resp.status_code})."
    except Exception as e:
        return f"Fehler bei der Wortsuche: {e}"


def search_emoji(query):
    if not query:
        return "Bitte gib einen Suchbegriff für Emojis an."
    try:
        url = f"https://emoji-api.com/emojis?search={quote(query)}&access_key=no-key"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                emojis = [f"{e.get('character', '')} - {e.get('unicodeName', e.get('slug', ''))}" for e in data[:10]]
                return "Emojis:\n" + "\n".join(emojis)
        return f"Keine Emojis zu '{query}' gefunden."
    except Exception as e:
        return f"Fehler bei Emoji-Suche: {e}"


def generate_qrcode(text):
    if not text:
        return "Bitte gib einen Text oder eine URL für den QR-Code an."
    encoded = quote(text)
    return f"QR-Code für '{text}':\nhttps://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded}"


def ping_url(target):
    if not target:
        return "Bitte gib eine URL oder Domain an."
    url = normalize_url(target)
    try:
        start = datetime.datetime.now()
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        elapsed = (datetime.datetime.now() - start).total_seconds()
        return f"PING {resp.url}\nStatus: {resp.status_code}\nZeit: {elapsed:.2f}s\nGröße: {len(resp.content)} Bytes"
    except Exception as e:
        return f"Fehler bei PING: {e}"


def random_number(arg):
    parts = arg.strip().split()
    try:
        min_n = int(parts[0]) if len(parts) > 0 else 1
        max_n = int(parts[1]) if len(parts) > 1 else 100
        if min_n > max_n:
            min_n, max_n = max_n, min_n
        result = random.randint(min_n, max_n)
        return f"Zufallszahl ({min_n}-{max_n}): {result}"
    except (ValueError, IndexError):
        return f"Bitte gib Bereich an, z.B. 1 100"


def word_count(text):
    if not text:
        return "Bitte gib einen Text ein."
    words = text.split()
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    lines = text.count("\n") + 1
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    return f"Wörter: {len(words)}\nZeichen: {chars}\nZeichen (ohne Leerzeichen): {chars_no_space}\nZeilen: {lines}\nSätze: {sentences}"


def format_json_text(argument):
    if not argument:
        return "Bitte gib JSON-Text zum Formatieren an."
    try:
        parsed = json.loads(argument)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        return f"Formatiertes JSON:\n{formatted}"
    except json.JSONDecodeError as e:
        return f"Ungültiges JSON: {e}"


def convert_units(argument):
    parts = argument.strip().split()
    if len(parts) < 3:
        units = {
            "laenge": "mm, cm, m, km, inch, foot, yard, mile",
            "gewicht": "mg, g, kg, t, lb, oz",
            "temperatur": "c, f, k",
            "volumen": "ml, l, gal, qt, floz",
        }
        return "Bitte: <Wert> <von> <nach>\n" + "\n".join(f"  {k}: {v}" for k, v in units.items())
    try:
        value = float(parts[0])
        fr = parts[1].lower()
        to = parts[2].lower()
        length_units = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "inch": 0.0254, "foot": 0.3048, "yard": 0.9144, "mile": 1609.344}
        weight_units = {"mg": 0.001, "g": 1.0, "kg": 1000.0, "t": 1000000.0, "lb": 453.592, "oz": 28.3495}
        if fr in length_units and to in length_units:
            result = value * length_units[fr] / length_units[to]
            return f"{value} {fr} = {result:.4f} {to}"
        if fr in weight_units and to in weight_units:
            result = value * weight_units[fr] / weight_units[to]
            return f"{value} {fr} = {result:.4f} {to}"
        if fr in ("c", "f", "k") and to in ("c", "f", "k"):
            celsius = value
            if fr == "f":
                celsius = (value - 32) * 5 / 9
            elif fr == "k":
                celsius = value - 273.15
            if to == "c":
                result = celsius
            elif to == "f":
                result = celsius * 9 / 5 + 32
            else:
                result = celsius + 273.15
            return f"{value}°{fr.upper()} = {result:.2f}°{to.upper()}"
        return f"Unbekannte Einheiten: {fr}, {to}. Verfügbar: Länge, Gewicht, Temperatur"
    except ValueError:
        return "Ungültiger Zahlenwert."
    except Exception as e:
        return f"Fehler: {e}"


def unix_timestamp(argument):
    if not argument:
        now = datetime.datetime.now()
        return f"Aktuell: {int(now.timestamp())} (Unix: {now.strftime('%d.%m.%Y %H:%M:%S')})"
    try:
        ts = int(argument)
        dt = datetime.datetime.fromtimestamp(ts)
        return f"{ts} -> {dt.strftime('%d.%m.%Y %H:%M:%S')}"
    except (ValueError, OSError):
        try:
            dt = datetime.datetime.strptime(argument, "%d.%m.%Y")
            return f"{argument} -> Unix: {int(dt.timestamp())}"
        except ValueError:
            try:
                dt = datetime.datetime.strptime(argument, "%d.%m.%Y %H:%M:%S")
                return f"{argument} -> Unix: {int(dt.timestamp())}"
            except ValueError:
                return f"Bitte Unix-Timestamp oder Datum (dd.mm.yyyy oder dd.mm.yyyy HH:MM:SS)"


def number_base(argument):
    if not argument:
        return "Bitte gib eine Zahl an."
    try:
        num = int(argument.strip(), 0)
        return f"Dezimal: {num}\nBinär: {bin(num)}\nHex: {hex(num)}\nOktal: {oct(num)}"
    except ValueError:
        return f"Ungültige Zahl: {argument}"


def ascii_codes(text):
    if not text:
        return "Bitte gib Text an."
    lines = []
    for ch in text[:50]:
        lines.append(f"'{ch}' -> {ord(ch)} (0x{ord(ch):02x})")
    return "ASCII/Unicode-Codes:\n" + "\n".join(lines)


def random_joke():
    try:
        resp = requests.get("https://v2.jokeapi.dev/joke/Programming?lang=de&safe-mode", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("type") == "single":
                return data.get("joke", "Kein Witz gefunden.")
            return f"{data.get('setup', '')}\n{data.get('delivery', '')}"
        return "Konnte keinen Witz laden."
    except Exception:
        try:
            resp = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return f"{data.get('setup', '')}\n{data.get('punchline', '')}"
        except Exception:
            pass
        return "Witze-API nicht erreichbar."


# ====================================================================
# NEUE TOOLS - Kostenlose Web-APIs (kein API-Key nötig)
# ====================================================================

def get_country_info(country_name):
    """Hole Länderdaten: Hauptstadt, Flagge, Währung."""
    if not country_name:
        return "Bitte gib ein Land an, z.B. COUNTRY Germany"
    try:
        # countriesnow.space API (kein Key nötig)
        search = country_name.strip().lower()
        url = "https://countriesnow.space/api/v0.1/countries/info?returns=currency,flag,capital"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for c in data:
                if c.get("name", "").lower() == search:
                    name = c.get("name", "?")
                    capital = c.get("capital", "?")
                    currency = c.get("currency", "?")
                    flag_url = c.get("flag", "")
                    return (f"🏳️ {name}\n"
                            f"🏙️ Hauptstadt: {capital}\n"
                            f"💰 Währung: {currency}\n"
                            f"🖼️ Flagge: {flag_url}")
            # Falls nicht exakt gefunden, Teilübereinstimmung suchen
            for c in data:
                if search in c.get("name", "").lower():
                    name = c.get("name", "?")
                    capital = c.get("capital", "?")
                    currency = c.get("currency", "?")
                    flag_url = c.get("flag", "")
                    return (f"🏳️ {name}\n"
                            f"🏙️ Hauptstadt: {capital}\n"
                            f"💰 Währung: {currency}\n"
                            f"🖼️ Flagge: {flag_url}")
        return f"❌ Land '{country_name}' nicht gefunden."
    except Exception as e:
        return f"Fehler bei Ländersuche: {e}"


def get_dad_joke(_=None):
    """Hole einen zufälligen Papa-Witz (icanhazdadjoke)."""
    try:
        resp = requests.get("https://icanhazdadjoke.com/",
                           headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return f"😂 {data.get('joke', 'Kein Witz gefunden.')}"
        return "Konnte keinen Papa-Witz laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_advice(_=None):
    """Hole einen zufälligen Ratschlag."""
    try:
        resp = requests.get("https://api.adviceslip.com/advice", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            slip = data.get("slip", {})
            return f"💡 Ratschlag #{slip.get('id', '?')}: {slip.get('advice', 'Kein Ratschlag.')}"
        return "Konnte keinen Ratschlag laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_quote(_=None):
    """Hole ein zufälliges Zitat."""
    try:
        resp = requests.get("https://zenquotes.io/api/random", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                q = data[0]
                return f"📝 \"{q.get('q', '')}\"\n   — {q.get('a', 'Unbekannt')}"
        return "Konnte kein Zitat laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_number_fact(argument):
    """Hole einen interessanten Fakt über eine Zahl (via UselessFacts Fallback)."""
    num = argument.strip() if argument else "42"
    try:
        # Versuche zuerst uselessfacts
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
                           timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🔢 Fakt zu '{num}': {data.get('text', 'Kein Fakt.')}"
        return f"🔢 Lustiger Fakt zu '{num}': Die Zahl {num} ist interessant, aber ich konnte keinen speziellen Fakt laden."
    except Exception as e:
        return f"🔢 Die Zahl {num} ist eine tolle Zahl! Leider kein API-Fakt: {e}"


def get_bored_activity(_=None):
    """Schlage eine Aktivität vor wenn einem langweilig ist."""
    # Versuche mehrere APIs als Fallback
    for url in [
        "https://www.boredapi.com/api/activity",
        "http://www.boredapi.com/api/activity",
    ]:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                price_val = data.get('price', 0)
                price_str = "Kostenlos" if price_val == 0 else f"${price_val*100:.0f}"
                return (f"🎯 Aktivität: {data.get('activity', '?')}\n"
                        f"📋 Typ: {data.get('type', '?')}\n"
                        f"👥 Teilnehmer: {data.get('participants', '?')}\n"
                        f"💰 Preis: {price_str}")
        except Exception:
            continue
    # Fallback: Nutzlosen Fakt als Aktivität
    try:
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
                           timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🎯 Wie wär's mit: {data.get('text', 'Irgendwas Neues ausprobieren?')}"
    except Exception:
        pass
    return "🎯 Wie wär's mit: Einem neuen Hobby nachgehen? Oder mal was ganz Neues ausprobieren!"


def get_useless_fact(_=None):
    """Hole einen nutzlosen Fakt."""
    try:
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
                           timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🤔 {data.get('text', 'Kein Fakt.')}"
        return "Konnte keinen Fakt laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_cat_fact(_=None):
    """Hole einen zufälligen Katzen-Fakt."""
    try:
        resp = requests.get("https://catfact.ninja/fact", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🐱 {data.get('fact', 'Kein Fakt.')}"
        return "Konnte keinen Katzen-Fakt laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_chuck_norris_joke(_=None):
    """Hole einen Chuck Norris Witz."""
    try:
        resp = requests.get("https://api.chucknorris.io/jokes/random", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🥋 {data.get('value', 'Kein Witz.')}"
        return "Konnte keinen Chuck Norris Witz laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_crypto_price(coin):
    """Hole aktuellen Cryptocurrency-Preis via CoinGecko."""
    if not coin:
        return "Bitte gib eine Coin-ID an, z.B. COINGECKO bitcoin"
    try:
        coin = coin.strip().lower()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={quote(coin)}&vs_currencies=usd,eur&include_24hr_change=true"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if coin in data:
                c = data[coin]
                usd = c.get("usd", "?")
                eur = c.get("eur", "?")
                change = c.get("usd_24h_change", 0)
                arrow = "📈" if change is not None and change >= 0 else "📉"
                base = f"💰 {coin.upper()}\nUSD: ${usd:,}\nEUR: €{eur:,}"
                if change is not None:
                    base += f"\n24h: {arrow} {change:.2f}%"
                return base
            ähnliche = get_similar_coins(coin)
            return f"❌ '{coin}' nicht gefunden.{' Meintest du: ' + ähnliche if ähnliche else ''}"
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler bei Crypto-Preis: {e}"


def get_similar_coins(coin):
    """Hilfsfunktion: Finde ähnliche Coin-Namen."""
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/coins/list", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            coins = resp.json()
            matches = [c["id"] for c in coins if coin in c["id"].lower()]
            if matches:
                return ", ".join(matches[:5])
    except Exception:
        pass
    return ""


def get_pokemon_info(name):
    """Hole Informationen zu einem Pokémon."""
    if not name:
        return "Bitte gib einen Pokémon-Namen an, z.B. POKEMON pikachu"
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{quote(name.strip().lower())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            name_o = data.get("name", "?").capitalize()
            types = ", ".join([t["type"]["name"].capitalize() for t in data.get("types", [])])
            stats = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}
            abilities = ", ".join([a["ability"]["name"].capitalize() for a in data.get("abilities", [])[:3]])
            height = data.get("height", 0) / 10
            weight = data.get("weight", 0) / 10
            return (f"⚡ {name_o}\n"
                    f"📖 Typ: {types}\n"
                    f"❤️ HP: {stats.get('hp', '?')} | ⚔️ Angriff: {stats.get('attack', '?')}\n"
                    f"🛡️ Verteidigung: {stats.get('defense', '?')} | 💨 Speed: {stats.get('speed', '?')}\n"
                    f"📏 Größe: {height:.1f}m | ⚖️ Gewicht: {weight:.1f}kg\n"
                    f"🎯 Fähigkeiten: {abilities}")
        return f"❌ Pokémon '{name}' nicht gefunden."
    except Exception as e:
        return f"Fehler bei Pokémon-Suche: {e}"


def get_swapi_info(character):
    """Hole Informationen zu einem Star Wars Charakter."""
    if not character:
        return "Bitte gib einen Star Wars Charakter an, z.B. SWAPI luke"
    try:
        url = f"https://swapi.dev/api/people/?search={quote(character.strip())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                p = results[0]
                return (f"⭐ {p.get('name', '?')}\n"
                        f"📏 Größe: {p.get('height', '?')}cm\n"
                        f"⚖️ Gewicht: {p.get('mass', '?')}kg\n"
                        f"👁️ Augen: {p.get('eye_color', '?')}\n"
                        f"💇 Haare: {p.get('hair_color', '?')}\n"
                        f"🌍 Heimat-Planet: {p.get('homeworld', '?')}\n"
                        f"📅 Geburtsjahr: {p.get('birth_year', '?')}")
            return f"❌ Charakter '{character}' nicht gefunden."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler bei SWAPI: {e}"


def get_tv_show_info(show):
    """Hole Informationen zu einer TV-Serie."""
    if not show:
        return "Bitte gib eine Serie an, z.B. TVSHOW breaking bad"
    try:
        url = f"https://api.tvmaze.com/search/shows?q={quote(show.strip())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if data:
                s = data[0].get("show", {})
                name = s.get("name", "?")
                status = s.get("status", "?")
                genres = ", ".join(s.get("genres", [])) or "?"
                rating = s.get("rating", {}).get("average", "?")
                premiered = s.get("premiered", "?")
                language = s.get("language", "?")
                summary = s.get("summary", "")
                summary_clean = html_to_text(summary)[:300] if summary else "Keine Beschreibung."
                url_show = s.get("url", "?")
                return (f"📺 {name}\n"
                        f"📅 Premiere: {premiered}\n"
                        f"📊 Status: {status}\n"
                        f"🏷️ Genres: {genres}\n"
                        f"⭐ Bewertung: {rating}/10\n"
                        f"🌐 Sprache: {language}\n"
                        f"📝 {summary_clean}\n"
                        f"🔗 {url_show}")
            return f"❌ Serie '{show}' nicht gefunden."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler bei TV-Suche: {e}"


def get_gender_from_name(name):
    """Rate das Geschlecht aus einem Vornamen (Genderize.io)."""
    if not name:
        return "Bitte gib einen Namen an, z.B. GENDERIZE alex"
    try:
        url = f"https://api.genderize.io/?name={quote(name.strip().lower())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            gender = data.get("gender", "unbekannt")
            prob = data.get("probability", 0) * 100
            count = data.get("count", 0)
            if gender:
                emoji = "👨" if gender == "male" else "👩"
                return f"{emoji} {name.capitalize()} → {gender} ({prob:.0f}% Wahrscheinlichkeit, basierend auf {count} Datensätzen)"
            return f"❌ Keine Daten für '{name}'."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler: {e}"


def get_age_from_name(name):
    """Rate das Alter aus einem Vornamen (Agify.io)."""
    if not name:
        return "Bitte gib einen Namen an, z.B. AGIFY john"
    try:
        url = f"https://api.agify.io/?name={quote(name.strip().lower())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            age = data.get("age")
            count = data.get("count", 0)
            if age:
                return f"🎂 {name.capitalize()} → geschätztes Alter: {age} (basierend auf {count} Datensätzen)"
            return f"❌ Keine Daten für '{name}'."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler: {e}"


def get_iss_position(_=None):
    """Hole die aktuelle Position der ISS."""
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            pos = data.get("iss_position", {})
            lat = pos.get("latitude", "?")
            lon = pos.get("longitude", "?")
            ts = data.get("timestamp", "?")
            dt = datetime.datetime.fromtimestamp(ts) if isinstance(ts, int) else "?"
            return (f"🛰️ ISS Position\n"
                    f"🌐 Breite: {lat}\n"
                    f"🌐 Länge: {lon}\n"
                    f"🕐 Zeit: {dt}")
        return "Konnte ISS-Position nicht abrufen."
    except Exception as e:
        return f"Fehler: {e}"


def get_my_ip(_=None):
    """Hole die eigene öffentliche IP-Adresse."""
    try:
        resp = requests.get("https://api.ipify.org?format=json", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"🌐 Deine öffentliche IP: {data.get('ip', '?')}"
        return "Konnte IP nicht abrufen."
    except Exception as e:
        return f"Fehler: {e}"


def get_random_user(_=None):
    """Hole einen zufälligen Fake-Benutzer."""
    try:
        resp = requests.get("https://randomuser.me/api/", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            user = data.get("results", [{}])[0]
            name = f"{user.get('name', {}).get('first', '?')} {user.get('name', {}).get('last', '?')}"
            gender = user.get("gender", "?")
            email = user.get("email", "?")
            country = user.get("location", {}).get("country", "?")
            phone = user.get("phone", "?")
            pic = user.get("picture", {}).get("thumbnail", "?")
            return (f"👤 {name} ({gender})\n"
                    f"📧 {email}\n"
                    f"🌍 {country}\n"
                    f"📞 {phone}\n"
                    f"🖼️ {pic}")
        return "Konnte keinen Benutzer laden."
    except Exception as e:
        return f"Fehler: {e}"


def get_excuse(_=None):
    """Hole eine zufällige Ausrede."""
    excuses = [
        "Mein Hund hat meine Hausaufgaben gefressen.",
        "Der Verkehr war schrecklich.",
        "Mein Wecker hat nicht geklingelt.",
        "Ich war krank.",
        "Mein Internet war down.",
        "Ich habe die Zeit vergessen.",
        "Das war ein technischer Fehler.",
        "Ich dachte, das war für morgen.",
        "Mein Computer ist abgestürzt.",
        "Ich habe die E-Mail nicht bekommen.",
        "Der Zug hatte Verspätung.",
        "Ich musste dringend weg.",
        "Das gehört nicht zu meinen Aufgaben.",
        "Ich habe auf eine wichtige Antwort gewartet.",
        "Die Batterien waren leer.",
    ]
    try:
        resp = requests.get("https://excuser.herokuapp.com/v1/excuse", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                excuse = data[0]
                return f"🙈 {excuse.get('excuse', 'Keine Ausrede.')} (Kategorie: {excuse.get('category', '?')})"
    except Exception:
        pass
    return f"🙈 {random.choice(excuses)}"


def get_earthquake_info(_=None):
    """Hole aktuelle Erdbeben-Daten (Magnitude 4.5+)."""
    try:
        url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?"
               "format=geojson&minmagnitude=4.5&limit=5&orderby=magnitude")
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if not features:
                return "Keine aktuellen Erdbeben (Magnitude 4.5+)."
            results = []
            for eq in features[:5]:
                prop = eq.get("properties", {})
                mag = prop.get("mag", "?")
                place = prop.get("place", "?")
                time_ts = prop.get("time", 0) / 1000
                time_str = datetime.datetime.fromtimestamp(time_ts).strftime("%d.%m.%Y %H:%M")
                results.append(f"🌊 M{mag} - {place} ({time_str})")
            return "Aktuelle Erdbeben (M4.5+):\n" + "\n".join(results)
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler: {e}"


def get_dictionary_en(word):
    """Englisch-Wörterbuch: Definitionen, Beispiele, Phonetik."""
    if not word:
        return "Bitte gib ein englisches Wort an, z.B. DICTIONARY hello"
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(word.strip().lower())}"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                word_name = entry.get("word", word)
                phonetic = entry.get("phonetic", entry.get("phonetics", [{}])[0].get("text", ""))
                lines = [f"📖 {word_name} {phonetic}"]
                for m in entry.get("meanings", [])[:3]:
                    pos = m.get("partOfSpeech", "")
                    for d in m.get("definitions", [])[:2]:
                        definition = d.get("definition", "")
                        example = d.get("example", "")
                        line = f"  [{pos}] {definition}"
                        if example:
                            line += f"\n    📌 \"{example}\""
                        lines.append(line)
                return "\n".join(lines)
            return f"❌ Keine Definition für '{word}' gefunden."
        elif resp.status_code == 404:
            return f"❌ Wort '{word}' nicht im Wörterbuch gefunden."
        return f"Fehler: HTTP {resp.status_code}"
    except Exception as e:
        return f"Fehler: {e}"


def show_memory_content(author):
    try:
        if author:
            memory_file, _ = get_user_memory_paths(author)
        else:
            project_root = PROJECT_ROOT
            memory_file = os.path.join(project_root, "Agent", "Memorys", "terminal_memory.txt")
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            return f"Gespeicherte Memory:\n{content}" if content.strip() else "Memory ist leer."
        return "Keine Memory-Datei gefunden."
    except Exception as e:
        return f"Fehler: {e}"


def memory_test(argument):
    """Testet ob Memory gelesen, geändert oder hinzugefügt werden kann.
    
    Aktionen:
    - read: Zeigt aktuelles Memory
    - add <text>: Fügt eine Test-Notiz hinzu (mit Bestätigungsfrage)
    - clear: Entfernt Test-Notizen
    - full: Führt alle Tests durch
    """
    if not argument:
        return (
            "Memory-Test — Nutze: TOOL: MEMORYTEST <aktion>\n"
            "Aktionen:\n"
            "  read           Zeigt aktuelles Memory\n"
            "  add <text>     Testet ob neue Inhalte gespeichert werden können\n"
            "  clear          Entfernt Test-Einträge\n"
            "  full           Führt vollständigen Lese/Schreib/Lösch-Test durch"
        )
    
    parts = argument.strip().split(None, 1)
    action = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    
    project_root = PROJECT_ROOT
    memory_file = os.path.join(project_root, "Agent", "Memorys", "terminal_memory.txt")
    
    if action == "read":
        if not os.path.exists(memory_file):
            return "❌ Memory-Datei existiert nicht."
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                return f"📖 Memory-Inhalt:\n{content}"
            else:
                return "📖 Memory ist leer."
        except Exception as e:
            return f"❌ Lesefehler: {e}"
    
    elif action == "add":
        if not rest:
            return "❌ Bitte gib einen Text zum Hinzufügen an.\nBeispiel: TOOL: MEMORYTEST add Das ist ein Test"
        test_entry = f"[MEMORYTEST {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}] {rest}"
        try:
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(test_entry + "\n")
            # Prüfen ob es wirklich geschrieben wurde
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            if test_entry in content:
                return f"✅ Memory erfolgreich geändert! Test-Eintrag hinzugefügt:\n{test_entry}"
            else:
                return "❌ Schreibtest fehlgeschlagen – Eintrag wurde nicht gespeichert."
        except Exception as e:
            return f"❌ Schreibfehler: {e}"
    
    elif action == "clear":
        if not os.path.exists(memory_file):
            return "Keine Memory-Datei gefunden."
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            cleaned = [l for l in lines if not l.startswith("[MEMORYTEST")]
            with open(memory_file, "w", encoding="utf-8") as f:
                f.writelines(cleaned)
            removed = len(lines) - len(cleaned)
            return f"🧹 {removed} Test-Einträge entfernt."
        except Exception as e:
            return f"❌ Fehler beim Bereinigen: {e}"
    
    elif action == "full":
        results = []
        # 1. Lesetest
        results.append("▶️  Test 1: Memory lesen")
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            results.append("   ✅ Lesen erfolgreich" if os.path.exists(memory_file) else "   ⚠️  Datei neu erstellt")
        except Exception as e:
            results.append(f"   ❌ Lesefehler: {e}")
        
        # 2. Schreibtest
        test_stamp = f"[MEMORYTEST {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Volltest"
        results.append("▶️  Test 2: Memory schreiben")
        try:
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(test_stamp + "\n")
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read()
            if test_stamp in content:
                results.append("   ✅ Schreiben erfolgreich")
            else:
                results.append("   ❌ Schreibtest fehlgeschlagen")
        except Exception as e:
            results.append(f"   ❌ Schreibfehler: {e}")
        
        # 3. Löschtest (nur unseren Eintrag)
        results.append("▶️  Test 3: Memory ändern (löschen)")
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            before = len(lines)
            cleaned = [l for l in lines if l.strip() != test_stamp]
            with open(memory_file, "w", encoding="utf-8") as f:
                f.writelines(cleaned)
            if len(cleaned) < before:
                results.append("   ✅ Löschen erfolgreich")
            else:
                results.append("   ⚠️  Nichts zu löschen")
        except Exception as e:
            results.append(f"   ❌ Löschfehler: {e}")
        
        results.append("\n📋 Zusammenfassung: Memory ist voll funktionsfähig.")
        return "\n".join(results)
    
    else:
        return f"Unbekannte Aktion: {action}. Verfügbar: read, add, clear, full"


def parse_tool_shortcut(text):
    if not text:
        return None, None
    parts = text.strip().split(None, 2)
    if len(parts) < 1:
        return None, None
    prefix = parts[0].lower().rstrip(":")

    # Buchstaben-Shortcuts: !s = !tool SEARCH
    _SHORTCUTS = {
        "!s": "!tool SEARCH", "!b": "!tool BROWSE", "!w": "!tool WIKI",
        "!n": "!tool NEWS", "!p": "!tool WEATHER", "!r": "!tool RESEARCH",
        "!d": "!tool DEEPRESEARCH", "!t": "!tool TRANSLATE",
        "!l": "!tool LIST",
        "!c": "!tool COUNTRY", "!co": "!tool COINGECKO",
        "!j": "!tool DADJOKE", "!q": "!tool QUOTE",
        "!cn": "!tool CHUCKNORRIS", "!pi": "!tool POKEMON",
        "!sw": "!tool SWAPI", "!tv": "!tool TVSHOW",
        "!iss": "!tool ISS", "!ip": "!tool MYIP",
        "!g": "!tool GENDERIZE", "!a": "!tool AGIFY",
        "!dic": "!tool DICTIONARY",
    }
    if prefix in _SHORTCUTS:
        new_text = _SHORTCUTS[prefix]
        if len(parts) > 1:
            new_text += " " + " ".join(parts[1:])
        return parse_tool_shortcut(new_text)

    # !do / !mach → an KI delegieren (einfach None zurück, fällt durch)
    if prefix in ("!do", "!mach"):
        return None, None

    # !tools / !help / !tool → Tools-Liste oder Einzel-Tool
    if prefix in ("!tools", "!tool", "tool", "!help", "help"):
        if len(parts) == 1:
            return "TOOLS", ""
        tool_name = parts[1].upper()
        arg = parts[2] if len(parts) > 2 else ""
        return tool_name, arg
    return None, None


# Tools, die KEINE Argumente benötigen
TOOLS_WITHOUT_ARGS = {"DATE", "UUID", "JOKE", "MEMORY", "TOOLS", "HELP",
                       "DADJOKE", "ADVICE", "QUOTE", "USELESSFACT", "CATFACT",
                       "CHUCKNORRIS", "ISS", "MYIP", "BORED", "RANDOMUSER",
                       "EXCUSE", "EARTHQUAKE", "DOG", "CAT", "FOX", "RIDDLE",
                       "KANYE", "SPACEFLIGHT", "TRIVIA", "INSPIRE", "BITCOIN"}

# Tools, die ARGUMENTE ERWARTEN (für Validierung)
TOOLS_REQUIRING_ARGS = {
    "HASH": "Algorithmus (md5/sha256) und Text",
    "MATH": "einen Ausdruck (z.B. sin(pi/2))",
    "SHORTEN": "eine URL",
    "REMIND": "Sekunden und Nachricht",
    "DEEPRESEARCH": "ein Thema zur tiefgreifenden Recherche",
    "SEARCH": "eine Suchanfrage",
    "BROWSE": "eine URL",
    "NEWS": "ein Thema",
    "RECIPE": "eine Suchanfrage",
    "WIKI": "ein Thema",
    "PASSWORD": "eine gewünschte Länge (oder leer lassen für Standard)",
    "PRICE": "ein Produkt",
    "FILESEARCH": "einen Dateinamen oder Suchbegriff",
    "RESEARCH": "ein Thema",
    "WEATHER": "einen Ort",
    "URLINFO": "eine URL",
    "EXTRACTLINKS": "eine URL",
    "META": "eine URL",
    "PAGEWORDS": "eine URL",
    "FORMINFO": "eine URL",
    "SUBMITFORM": "eine URL, Formularnummer und Felder",
    "CLICK": "eine URL und optional Linktext/Nummer",
    "SUMMARIZE": "eine URL oder einen Dateipfad",
    "CALC": "einen mathematischen Ausdruck",
    "TIME": "optional einen Ort (leer = aktuelle Zeit)",
    "DICEROLL": "eine Würfelangabe (z.B. 3d6)",
    "BASE64": "'encode' oder 'decode' und den Text",
    "IPINFO": "optional eine IP-Adresse (leer = eigene IP)",
    "CURRENCY": "Betrag, Quellwährung und Zielwährung",
    "EMOJI": "einen Suchbegriff",
    "QRCODE": "einen Text oder eine URL",
    "DEFINE": "ein Wort",
    "TRANSLATE": "einen Text (optional mit Sprachangabe z.B. en->de: Text)",
    "PING": "eine URL oder Domain",
    "RANDOM": "Minimal- und Maximalwert",
    "WORDCOUNT": "einen Text",
    "FORMATJSON": "JSON-Text",
    "UNITS": "Wert, Ausgangseinheit und Zieleinheit",
    "TIMESTAMP": "optional einen Unix-Timestamp oder ein Datum",
    "BIN": "eine Zahl",
    "ASCII": "einen Text",
    "MEMORYTEST": "eine Aktion (read, add, clear, full)",
    "LIST": "ein Thema für die Listenerstellung",
    "COUNTRY": "ein Land (z.B. Germany)",
    "NUMBERS": "eine Zahl (optional, leer = zufällig)",
    "COINGECKO": "eine Coin-ID (z.B. bitcoin, ethereum)",
    "POKEMON": "ein Pokémon-Name (z.B. pikachu)",
    "SWAPI": "ein Star Wars Charakter (z.B. luke)",
    "TVSHOW": "eine TV-Serie (z.B. breaking bad)",
    "GENDERIZE": "ein Vorname (z.B. alex)",
    "AGIFY": "ein Vorname (z.B. john)",
    "DICTIONARY": "ein englisches Wort (z.B. hello)",
    "GITHUB": "ein GitHub-Username (z.B. torvalds)",
    "PYPISEARCH": "ein PyPI-Paketname (z.B. requests)",
    "COCKTAIL": "optional ein Cocktailname (leer = zufällig)",
    "JOKEAPI": "optional eine Kategorie (Any, Programming, Pun, Dark)",
    "UNIVERSITY": "ein Universitätsname (z.B. Harvard)",
    "LYRICS": "'Artist - Title' (z.B. Queen - Bohemian Rhapsody)",
}

def get_tool_param_requirement(tool_name):
    """Gibt zurück ob ein Tool Argumente braucht und welche."""
    tool_name = tool_name.upper()
    if tool_name in TOOLS_WITHOUT_ARGS:
        return "none", None
    if tool_name in TOOLS_REQUIRING_ARGS:
        return "optional" if tool_name in ("PASSWORD", "TIME", "IPINFO", "TIMESTAMP") else "required", TOOLS_REQUIRING_ARGS.get(tool_name)
    return "unknown", None


def run_tool_command(command, argument):
    if not command:
        return "Keine Tool-Anweisung gefunden."
    command = command.strip().upper()
    if command in ("HELP", "TOOLS", "TOOL"):
        return TOOL_HELP_TEXT
    if command.startswith("TOOL:"):
        command = command[5:].strip()
    
    # Prüfe ob das Tool existiert
    req_type, param_desc = get_tool_param_requirement(command)
    if req_type == "unknown":
        # Fuzzy-Matching + Vorschläge
        _ALL_TOOLS = list(TOOLS_REQUIRING_ARGS.keys()) + list(TOOLS_WITHOUT_ARGS)
        import difflib
        prefix = [t for t in _ALL_TOOLS if t.startswith(command)]
        if prefix:
            return handle_tool_command(f"TOOL: {prefix[0]}", argument)
        matches = difflib.get_close_matches(command, _ALL_TOOLS, n=3, cutoff=0.4)
        if matches:
            return f"Unbekanntes Tool: '{command}'. Meintest du: {', '.join(matches)}?"
    
    # Prüfe auf fehlende Pflichtparameter
    if req_type == "required" and not argument.strip():
        return f"❌ Für {command} fehlt ein Parameter.\nBitte gib an: {param_desc}.\nBeispiel: TOOL: {command} <wert>"
    
    return handle_tool_command(f"TOOL: {command}", argument)


def extract_tool_command(text):
    if not text:
        return None, None
    # TOOL: am Zeilenanfang erkennen
    m = re.search(r"(?:^|\n)\s*TOOL:\s*(\w+)\s*(.*)", text, re.I | re.M)
    if m:
        return f"TOOL: {m.group(1).upper()}", m.group(2).strip()
    # Auch !tool NAME <arg> im Text erkennen (für von der KI generierte Shortcuts)
    m = re.search(r"(?:^|\n)\s*!tool\s+(\w+)\s*(.*)", text, re.I | re.M)
    if m:
        return f"TOOL: {m.group(1).upper()}", m.group(2).strip()
    return None, None


def extract_all_tool_commands(text):
    """Extrahiert ALLE TOOL:-Befehle aus einem Text.
    Returns: Liste von (command, argument) -Tuplen, z.B. [("TOOL: DATE", ""), ("TOOL: WEATHER", "Berlin")]
    """
    if not text:
        return []
    results = []
    # Alle TOOL:-Zeilen finden
    for m in re.finditer(r"(?:^|\n)\s*TOOL:\s*(\w+)\s*(.*)", text, re.I | re.M):
        results.append((f"TOOL: {m.group(1).upper()}", m.group(2).strip()))
    # Auch !tool NAME <arg> finden
    for m in re.finditer(r"(?:^|\n)\s*!tool\s+(\w+)\s*(.*)", text, re.I | re.M):
        results.append((f"TOOL: {m.group(1).upper()}", m.group(2).strip()))
    return results


def generate_password(params):
    length = 16
    if params:
        match = re.search(r"(\d+)", params)
        if match:
            length = max(8, min(int(match.group(1)), 64))
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?/"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"Generiertes Passwort ({length} Zeichen): {password}"


def search_files(query):
    if not query:
        return "Bitte gib einen Dateinamen oder Suchbegriff an."
    # Nur alphanumerische Zeichen + Leerzeichen erlauben
    safe_query = re.sub(r"[^a-zA-Z0-9\s\-_\.]", "", query)
    if not safe_query:
        return "Ungültiger Suchbegriff. Nur Buchstaben, Zahlen und Punkte erlaubt."
    matches = []
    project_root = PROJECT_ROOT
    for root, dirs, files in os.walk(project_root):
        # node_modules und .git überspringen
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", ".venv")]
        for filename in files:
            if safe_query.lower() in filename.lower():
                matches.append(os.path.join(root, filename))
                if len(matches) >= 20:
                    break
        if len(matches) >= 20:
            break
    if not matches:
        return f"Kein Ergebnis für Dateisuche: {safe_query}"
    return "Gefundene Dateien:\n" + "\n".join(matches)


def get_weather(location):
    if not location:
        return "Bitte gib einen Ort für das Wetter an."

    # Datums-Keywords aus dem location-String extrahieren
    date_keywords = [
        "morgen", "übermorgen", "heute", "montag", "dienstag", "mittwoch",
        "donnerstag", "freitag", "samstag", "sonntag", "nächste", "tage",
        "woche", "wochenende", "next", "today", "tomorrow", "days", "week",
    ]
    # Orte von Datums-Keywords trennen
    words = location.split()
    clean_words = [w for w in words if w.lower().strip(",.!?") not in date_keywords]
    clean_location = " ".join(clean_words).strip()
    location_lower = location.lower()

    # Prüfen ob eine bestimmte Anzahl Tage oder ein Datum gewünscht ist
    day_count = 3  # default: 3 Tage
    day_match = re.search(r"(\d+)\s*(?:tage|tag)", location_lower)
    if day_match:
        day_count = min(int(day_match.group(1)), 7)

    try:
        # JSON-Daten von wttr.in abrufen
        json_url = f"https://wttr.in/{quote(clean_location or location)}?format=j1&lang=de"
        resp = requests.get(json_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_condition", [{}])[0]
        forecast = data.get("weather", [])

        if not forecast:
            return f"Keine Wetterdaten für '{location}' gefunden."

        # Aktuelles Wetter
        temp = current.get("temp_C", "?")
        feels = current.get("FeelsLikeC", "?")
        desc = current.get("lang_de", [{}])[0].get("value", "") or current.get("weatherDesc", [{}])[0].get("value", "")
        wind = current.get("windspeedKmph", "?")
        humidity = current.get("humidity", "?")
        cloud = current.get("cloudcover", "?")

        # Deutsche Wochentage (locale-unabhängig)
        DE_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        DE_DAYS_FULL = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

        def _fmt_time(t):
            """hh:mm AM/PM → hh:mm (24h)"""
            if not t or t == "?":
                return "?"
            m = re.match(r"(\d+):(\d+)\s*(AM|PM)", t)
            if m:
                h, mi, ap = int(m.group(1)), m.group(2), m.group(3)
                if ap == "PM" and h != 12:
                    h += 12
                elif ap == "AM" and h == 12:
                    h = 0
                return f"{h:02d}:{mi}"
            return t

        def _de_day(d):
            return DE_DAYS[d.weekday()]

        def _de_day_full(d):
            return DE_DAYS_FULL[d.weekday()]

        lines = []
        ort = clean_location or location or "(unbekannter Ort)"
        lines.append(f"--- Wetter für {ort} ---")
        lines.append(f"Aktuell: {temp}C (gefuehlt {feels}C), {desc}")
        lines.append(f"Wind: {wind} km/h  |  Luftfeuchte: {humidity}%  |  Bewoelkung: {cloud}%")
        lines.append("")

        target_day = None
        today = datetime.date.today()

        if "übermorgen" in location_lower:
            target_day = today + datetime.timedelta(days=2)
        elif any(w in location_lower for w in ["morgen", "tomorrow"]):
            target_day = today + datetime.timedelta(days=1)

        # Wochentag erkennen
        weekday_map = {
            "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
            "freitag": 4, "samstag": 5, "sonntag": 6, "monday": 0, "tuesday": 1,
            "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        }
        for w in words:
            w_clean = w.lower().strip(",.!?")
            if w_clean in weekday_map:
                wanted_weekday = weekday_map[w_clean]
                target_day = today + datetime.timedelta(days=(wanted_weekday - today.weekday() + 7) % 7)
                if target_day == today:
                    target_day += datetime.timedelta(days=7)
                break

        def _fmt_day_line(day):
            """Formatiert einen einzelnen Vorhersage-Tag ohne Sonderzeichen."""
            do = datetime.date.fromisoformat(day["date"])
            mx = day.get("maxtempC", "?")
            mn = day.get("mintempC", "?")
            dd = (day.get("hourly", [{}])[0].get("lang_de", [{}])[0].get("value", "")
                  if day.get("hourly") else "")
            sr = _fmt_time(day.get("astronomy", [{}])[0].get("sunrise", "?"))
            ss = _fmt_time(day.get("astronomy", [{}])[0].get("sunset", "?"))
            desc_part = f" - {dd}" if dd else ""
            return (f"  {_de_day(do)} {do.strftime('%d.%m')}: {mn}-{mx}C{desc_part}\n"
                    f"    Sonne {sr}-{ss}")

        # Wochenende?
        if "wochenende" in location_lower or "weekend" in location_lower:
            dts = (5 - today.weekday() + 7) % 7
            if dts == 0:
                dts = 7
            lines.append("--- Wochenende ---")
            for i in range(dts, min(dts + 2, len(forecast))):
                lines.append(_fmt_day_line(forecast[i]))
            return "\n".join(lines)

        # Einzelner Tag gewuenscht?
        if target_day:
            for day in forecast:
                if datetime.date.fromisoformat(day["date"]) == target_day:
                    mx = day.get("maxtempC", "?")
                    mn = day.get("mintempC", "?")
                    dd = (day.get("hourly", [{}])[0].get("lang_de", [{}])[0].get("value", "")
                          if day.get("hourly") else "")
                    sr = _fmt_time(day.get("astronomy", [{}])[0].get("sunrise", "?"))
                    ss = _fmt_time(day.get("astronomy", [{}])[0].get("sunset", "?"))
                    lines.append(f"--- {_de_day_full(target_day)}, {target_day.strftime('%d.%m.%Y')} ---")
                    if dd:
                        lines.append(f"  {dd}")
                    lines.append(f"  Temp: {mn}C - {mx}C")
                    lines.append(f"  Sonne: {sr} - {ss}")
                    return "\n".join(lines)
            return f"Keine Vorhersage fuer {_de_day_full(target_day)} ({target_day}) verfuegbar."

        # Default: Vorhersage fuer die naechsten X Tage
        nd = min(day_count, len(forecast))
        lines.append(f"--- Vorhersage naechste {nd} {'Tag' if nd == 1 else 'Tage'} ---")
        for i in range(nd):
            lines.append(_fmt_day_line(forecast[i]))

        return "\n".join(lines)

    except requests.exceptions.RequestException:
        return search_web(f"Wetter {location}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return search_web(f"Wetter {location}")


def summarize_content(target):
    if not target:
        return "Bitte gib eine URL oder einen Dateipfad für die Zusammenfassung an."
    # URL
    if re.match(r"^https?://", target):
        content = browse_url(target)
        if content.startswith("Fehler"):
            return content
        # simple summarization: first 500 chars and first 5 lines
        lines = [l for l in content.splitlines() if l.strip()]
        summary_lines = lines[:5]
        summary = "\n".join(summary_lines)
        if len(summary) < 500:
            summary = summary + "\n\n" + content[:500]
        return "Zusammenfassung (Webseite):\n" + summary
    # Lokale Datei (nur innerhalb des Projektverzeichnisses)
    project_root = PROJECT_ROOT
    abs_target = os.path.abspath(target)
    if not abs_target.startswith(project_root):
        return "Zugriff verweigert: Datei liegt außerhalb des Projektverzeichnisses."
    if target.lower().endswith('.pdf'):
        try:
            import PyPDF2

            text = []
            with open(target, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for p in reader.pages:
                    try:
                        text.append(p.extract_text() or '')
                    except Exception:
                        continue
            content = "\n".join(text)
            if not content.strip():
                return "Keine extrahierbaren Texte in der PDF gefunden."
            lines = [l for l in content.splitlines() if l.strip()]
            summary = "\n".join(lines[:10])
            return "Zusammenfassung (PDF):\n" + summary
        except Exception as e:
            return f"Fehler beim Verarbeiten der PDF: {e}"

    # local text file
    if os.path.exists(target) and os.path.isfile(target):
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if not content.strip():
                return "Die Datei enthält keinen lesbaren Text."
            lines = [l for l in content.splitlines() if l.strip()]
            summary = "\n".join(lines[:10]) if lines else content[:500]
            return "Zusammenfassung (Datei):\n" + summary
        except Exception as e:
            return f"Fehler beim Lesen der Datei: {e}"

    # fallback: try to open as URL
    return browse_url(target)


def _extract_ddg_result_links(html):
    """Extrahiert echte Ergebnis-URLs aus DuckDuckGo HTML."""
    urls = []
    # DuckDuckGo redirect links: //duckduckgo.com/l/?uddg=https%3A%2F%2F...
    for m in re.finditer(r'uddg=(https?%3A[^&"\']+)', html):
        decoded = unquote(m.group(1))
        if decoded not in urls:
            urls.append(decoded)
    # Fallback: direkte <a href>-Links
    if not urls:
        for m in re.finditer(r'<a[^>]+href=["\'](https?://[^"\']+)["\']', html):
            url = m.group(1)
            if url not in urls and "duckduckgo" not in url.lower():
                urls.append(url)
    return urls


# Einfacher In-Memory-Cache für wiederholte Aufrufe
_research_cache = {}
_research_cache_lock = threading.Lock()
_CACHE_TTL = 300  # 5 Minuten


def _cache_get(key):
    with _research_cache_lock:
        if key in _research_cache:
            ts, val = _research_cache[key]
            if datetime.datetime.now().timestamp() - ts < _CACHE_TTL:
                return val
            del _research_cache[key]
    return None


def _cache_set(key, val):
    with _research_cache_lock:
        _research_cache[key] = (datetime.datetime.now().timestamp(), val)
        # Cache-Größe begrenzen
        if len(_research_cache) > 50:
            oldest = sorted(_research_cache.keys(), key=lambda k: _research_cache[k][0])
            for k in oldest[:20]:
                del _research_cache[k]


def _browse_page(url, timeout=6):
    """Einzelseiten-Aufruf mit kurzem Timeout."""
    try:
        content = browse_url(url, timeout=timeout)
        if not content.startswith("Fehler") and len(content) > 80:
            return content[:400]
    except Exception:
        pass
    return None


def _optimize_search_query(raw_query):
    """KI optimiert den Suchbegriff für bessere Suchergebnisse."""
    try:
        resp = client.chat.completions.create(
            model="gemma-4-31b-it",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du verbesserst Suchanfragen für eine Websuche. "
                        "Gib NUR den verbesserten Suchbegriff zurück, maximal 10 Wörter, "
                        "in derselben Sprache wie die Anfrage. "
                        "Erweitere sinnvoll: ergänze fehlende Fachbegriffe, präzisiere vage Formulierungen. "
                        "Keine Erklärungen, kein Präfix, kein Fließtext – nur der Suchbegriff."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Optimieren für Websuche: {raw_query}",
                },
            ],
            temperature=0.2,
            max_tokens=50,
            timeout=5,
        )
        optimized = resp.choices[0].message.content.strip().strip('"').strip("'")
        if optimized and len(optimized) > 5 and len(optimized) < 100:
            return optimized
    except Exception:
        pass
    return raw_query


def deep_research(topic):
    if not topic or not topic.strip():
        return "❌ Bitte gib ein Thema für die Recherche an."

    raw = topic.strip()
    # Cache-Check
    cached = _cache_get(raw.lower())
    if cached:
        return cached

    # 0. KI optimiert den Suchbegriff (parallel zur DuckDuckGo-Suche startbar, aber wir brauchen das Ergebnis zuerst)
    topic = _optimize_search_query(raw)

    # 1. DuckDuckGo-Suche + Wikipedia parallel
    result_urls = []
    search_sources = []
    wiki_text = ""

    def _search_ddg():
        nonlocal result_urls, search_sources
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": topic, "kl": "de-de"},
                headers=headers, timeout=8,
            )
            resp.raise_for_status()
            if resp.encoding and resp.encoding.lower() != "utf-8":
                resp.encoding = resp.apparent_encoding
            urls = _extract_ddg_result_links(resp.text)
            if urls:
                result_urls = urls[:6]
                search_sources.append("DuckDuckGo")
        except Exception:
            pass

    def _search_wiki():
        nonlocal wiki_text, result_urls, search_sources
        for lang in ("de", "en"):
            for wt in (topic.replace(" ", "_"), topic.lower().replace(" ", "_")):
                try:
                    raw_wiki = browse_url(f"https://{lang}.wikipedia.org/wiki/{quote(wt)}")
                    if not raw_wiki.startswith("Fehler") and len(raw_wiki) > 200:
                        wiki_text = raw_wiki[:800]
                        if not result_urls:
                            result_urls.append(f"https://{lang}.wikipedia.org/wiki/{quote(wt)}")
                            search_sources.append(f"Wikipedia ({lang})")
                        return
                except Exception:
                    continue

    threads = [threading.Thread(target=_search_ddg), threading.Thread(target=_search_wiki)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    # 2. Webseiten parallel browsen (max 2 – schnell, nicht perfekt)
    collected_texts = []
    if wiki_text:
        collected_texts.append(f"[Wikipedia]: {wiki_text}")

    browse_threads = []
    browse_count = min(len(result_urls), 2)
    browse_results = [None] * browse_count

    def _browse(idx, url):
        browse_results[idx] = _browse_page(url, timeout=5)

    for i, url in enumerate(result_urls[:browse_count]):
        t = threading.Thread(target=_browse, args=(i, url))
        browse_threads.append(t)
        t.start()
    for t in browse_threads:
        t.join(timeout=7)

    for r in browse_results:
        if r:
            collected_texts.append(r)

    # 3. KI fasst zusammen + Quellen
    source_info = ", ".join(search_sources) if search_sources else "Unbekannt"
    summary = _summarize_research(topic, collected_texts, result_urls, source_info)

    # Cache setzen
    _cache_set(raw.lower(), summary)
    return summary


def _summarize_research(topic, texts, urls, source_info="Unbekannt"):
    """Fasse die gesammelten Recherche-Inhalte per KI zusammen."""
    if not texts:
        return f"🔍 Zur **{topic}** konnte ich leider keine Quellen finden.\n\nVersuche es mit einem anderen Suchbegriff oder nutze `TOOL: SEARCH {topic}`."

    raw = "\n---\n".join(t for t in texts if t)
    if len(raw) > 3500:
        raw = raw[:3500].rsplit(" ", 1)[0] + " [...]"

    try:
        resp = client.chat.completions.create(
            model="gemma-4-31b-it",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein Recherche-Assistent. Fasse die folgenden Informationen strukturiert zusammen.\n\n"
                        "Regeln:\n"
                        "- Schreibe in DER SELBEN SPRACHE wie die Query\n"
                        "- Struktur: 1) Kurze Zusammenfassung (2-3 Sätze), 2) Wichtigste Punkte (bullet)\n"
                        "- Maximal 600 Zeichen\n"
                        "- Bleibe sachlich und faktenbasiert"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Thema: {topic}\n\nInformationen:\n{raw}",
                },
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=10,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception:
        summary = f"**Recherche zu: {topic}**\n\n"
        for i, t in enumerate(texts[:3], 1):
            summary += f"\n**Quelle {i}:**\n{t[:300]}...\n"

    # Quellen anhängen (kurz)
    summary += f"\n\n**Quellen ({source_info}):**\n"
    for url in urls[:4]:
        short = url[:60] + "..." if len(url) > 60 else url
        summary += f"- {short}\n"

    return summary.strip()


# ──────────────────────────────────────────
# HASH: Text hashen
# ──────────────────────────────────────────
def handle_hash(argument):
    if not argument:
        return "Nutze: HASH md5|sha1|sha256|sha512 <text>"
    algo, _, text = argument.partition(" ")
    algo = algo.lower()
    if not text:
        return f"Bitte Text fuer {algo} angeben."
    algos = {"md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256,
             "sha512": hashlib.sha512, "sha224": hashlib.sha224, "sha384": hashlib.sha384}
    if algo not in algos:
        return f"Unbekannt: {algo}. Verfuegbar: {', '.join(algos)}"
    return f"{algo.upper()}: {algos[algo](text.encode()).hexdigest()}"


# ──────────────────────────────────────────
# MATH: Erweiterter Rechner (ersetzt CALC)
# ──────────────────────────────────────────
_MATH_FUNCS = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt,
               "log": math.log, "log10": math.log10, "abs": abs, "round": round,
               "pi": math.pi, "e": math.e}

def handle_math(argument):
    if not argument:
        return "Nutze: MATH <ausdruck> z.B. MATH sin(pi/4) + sqrt(16)"
    s = re.sub(r"[^0-9a-zA-Z\.\+\-\*/\^\(\)\s\,]", "", argument).replace("^", "**").replace(",", ".")
    try:
        def _eval(node):
            if isinstance(node, ast.Expression): return _eval(node.body)
            if isinstance(node, ast.Constant): return float(node.value)
            if isinstance(node, ast.Name): return _MATH_FUNCS.get(node.id, 0)
            if isinstance(node, ast.Call):
                f = _MATH_FUNCS.get(node.func.id)
                return f(*[_eval(a) for a in node.args]) if f else 0
            if isinstance(node, ast.UnaryOp):
                return {ast.UAdd: lambda x: x, ast.USub: lambda x: -x}[type(node.op)](_eval(node.operand))
            if isinstance(node, ast.BinOp):
                ops = {ast.Add: lambda a,b:a+b, ast.Sub: lambda a,b:a-b, ast.Mult: lambda a,b:a*b,
                       ast.Div: lambda a,b:a/b, ast.Pow: lambda a,b:a**b, ast.Mod: lambda a,b:a%b}
                return ops[type(node.op)](_eval(node.left), _eval(node.right))
            raise ValueError
        return f"{argument} = {_eval(ast.parse(s, mode='eval')):g}"
    except Exception as e:
        return f"Fehler: {e}"


# ──────────────────────────────────────────
# SHORTEN: URL verkürzen
# ──────────────────────────────────────────
def handle_shorten(url):
    if not url:
        return "Nutze: SHORTEN <url>"
    if not url.startswith("http"):
        url = "https://" + url
    try:
        r = requests.post("https://is.gd/create.php", data={"format": "simple", "url": url}, timeout=8)
        if r.status_code == 200:
            return f"Kurz-URL: {r.text.strip()}"
        r2 = requests.get(f"https://tinyurl.com/api-create.php?url={quote(url)}", timeout=8)
        if r2.status_code == 200:
            return f"Kurz-URL: {r2.text.strip()}"
        return f"Fehler: Konnte URL nicht verkuerzen"
    except Exception as e:
        return f"Fehler: {e}"


# ──────────────────────────────────────────
# REMIND: Einmalige Erinnerung
# ──────────────────────────────────────────
def handle_remind(argument):
    if not argument:
        return "Nutze: REMIND <sekunden> <nachricht>"
    parts = argument.split(None, 1)
    try:
        sec = int(parts[0])
        msg = parts[1] if len(parts) > 1 else "Erinnerung!"
        if sec < 1 or sec > 86400:
            return "Zeitraum: 1-86400 Sekunden (max 24h)"
        threading.Thread(target=lambda: (time.sleep(sec), print(f"\n[ERINNERUNG] {msg}"))).start()
        return f"Erinnerung in {sec}s: '{msg[:60]}'"
    except ValueError:
        return "Bitte Sekunden angeben: REMIND 60 Pizza"


# ──────────────────────────────────────────
# LIST: Informationen als strukturierte Liste sammeln
# ──────────────────────────────────────────
def handle_list_tool(query):
    """Sammelt Informationen zu einem Thema aus dem Web und gibt sie als nummerierte Liste zurück."""
    if not query:
        return "Bitte gib ein Thema für die Liste an.\nBeispiel: TOOL: LIST Vorteile von Python"

    # ── 1. DuckDuckGo-HTML holen und echte Ergebnis-Snippets extrahieren ──
    snippets = []
    raw_html = None
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query, "kl": "de-de"},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        raw_html = resp.text

        # Snippet-Blöcke: <a class="result__a" ...>Titel</a>
        # gefolgt von <a class="result__snippet" ...>Snip</a>
        for m in re.finditer(
            r'(?is)<a[^>]*class="result__a"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            raw_html,
        ):
            title = html_to_text(m.group(1)).strip()
            snippet = html_to_text(m.group(2)).strip()
            combined = f"{title}: {snippet}" if title else snippet
            combined = re.sub(r"\s+", " ", combined).strip()
            if combined and len(combined) > 20 and combined not in snippets:
                snippets.append(combined)

        # Fallback: alternative Snippet-Klasse
        if len(snippets) < 3:
            for m in re.finditer(
                r'(?is)<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                raw_html,
            ):
                s = html_to_text(m.group(1)).strip()
                s = re.sub(r"\s+", " ", s)
                if s and len(s) > 20 and s not in snippets:
                    snippets.append(s)
    except Exception:
        pass

    # ── 2. Falls zu wenige Snippets: deep_research-Inhalte extrahieren ──
    if len(snippets) < 3:
        deep = deep_research(query)
        for line in deep.splitlines():
            line = line.strip()
            # Nur Zeilen mit Inhalt (>80 Zeichen) und ohne Schritt-Markierungen
            if len(line) > 80 and not line.startswith("[") and not line.startswith("=") and not line.startswith("-"):
                line = re.sub(r"\s+", " ", line)
                if line not in snippets:
                    snippets.append(line)

    # ── 3. Falls nichts gefunden: klassischen Suchtext filtern ──
    if len(snippets) < 3:
        _NOISE = {
            "all regions", "argentina", "australia", "austria", "belgium",
            "brazil", "bulgaria", "canada", "chile", "china", "colombia",
            "croatia", "czech republic", "denmark", "estonia", "finland",
            "france", "germany", "greece", "hungary", "india", "indonesia",
            "ireland", "israel", "italy", "japan", "latvia", "lithuania",
            "malaysia", "mexico", "netherlands", "new zealand", "nigeria",
            "norway", "peru", "philippines", "poland", "portugal", "romania",
            "russia", "saudi arabia", "serbia", "singapore", "slovakia",
            "slovenia", "south africa", "south korea", "spain", "sweden",
            "switzerland", "taiwan", "thailand", "turkey", "ukraine",
            "united kingdom", "united states", "vietnam",
            "settings", "themes", "privacy", "duckduckgo", "cookie",
            "datenschutz", "impressum", "anmelden", "registrieren",
            "akzeptieren", "feedback", "!bang",
        }
        text = html_to_text(raw_html) if raw_html else search_web(query)
        for line in text.splitlines():
            line = line.strip()
            if len(line) < 25:
                continue
            low = line.lower()
            if any(n in low for n in _NOISE):
                continue
            if line.count(",") >= 4 and all(len(w) < 20 for w in line.split(",")):
                continue
            if sum(c.isalpha() for c in line) < 15:
                continue
            line = re.sub(r"\s+", " ", line)
            if line not in snippets:
                snippets.append(line)

    if not snippets:
        return f"Keine strukturierten Informationen zu '{query}' gefunden."

    # ── 4. Liste formatieren ──
    result = [f"📋 Liste zu: {query}", "=" * (len(query) + 14), ""]
    for i, item in enumerate(snippets[:20], 1):
        item = item[:300]
        result.append(f"  {i:2d}. {item}")

    result.append(f"\n--- {len(snippets[:20])} Einträge gefunden ---")
    return "\n".join(result)


# ═══════════════════════════════════════════
# NEUE TOOLS
# ═══════════════════════════════════════════

def get_dog_image(breed=None):
    """Zufälliges Hundebild (dog.ceo)."""
    url = f"https://dog.ceo/api/breed/{breed}/images/random" if breed else "https://dog.ceo/api/breeds/image/random"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("message", "Kein Bild gefunden.")
    except Exception:
        return "Konnte kein Hundebild laden."

def get_cat_image(_=None):
    """Zufälliges Katzenbild (cataas)."""
    try:
        r = requests.get("https://cataas.com/cat?json=true", timeout=10)
        data = r.json()
        return f"https://cataas.com/cat/{data.get('_id', '')}"
    except Exception:
        return "Konnte kein Katzenbild laden."

def get_fox_image(_=None):
    """Zufälliges Fuchsbild."""
    try:
        r = requests.get("https://randomfox.ca/floof/", timeout=10)
        return r.json().get("image", "Kein Bild gefunden.")
    except Exception:
        return "Konnte kein Fuchsbild laden."

def get_riddle(_=None):
    """Zufälliges Rätsel (nur die Frage)."""
    try:
        r = requests.get("https://riddles-api.vercel.app/random", timeout=10)
        data = r.json()
        return f"🧩 Rätsel:\n\n{data.get('riddle', '?')}"
    except Exception:
        return "Konnte kein Rätsel laden."

def get_kanye_quote(_=None):
    """Zufälliges Kanye-West-Zitat."""
    try:
        r = requests.get("https://api.kanye.rest/", timeout=10)
        return f'Kanye: "{r.json().get("quote", "?")}"'
    except Exception:
        return "Konnte kein Kanye-Zitat laden."

def get_github_user(username):
    """GitHub-Benutzerinfo."""
    if not username:
        return "Bitte gib einen GitHub-Username an."
    try:
        r = requests.get(f"https://api.github.com/users/{quote(username)}", timeout=10)
        if r.status_code != 200:
            return f"GitHub-Benutzer '{username}' nicht gefunden."
        d = r.json()
        return (f"GitHub: {d.get('login')} ({d.get('name','?')})\n"
                f"Repos: {d.get('public_repos')} | Gists: {d.get('public_gists')}\n"
                f"Follower: {d.get('followers')} | Following: {d.get('following')}\n"
                f"Mitglied seit: {d.get('created_at','?')[:10]}\n"
                f"{d.get('html_url','')}")
    except Exception as e:
        return f"Fehler: {e}"

def get_pypi_package(package):
    """PyPI-Paketinfo."""
    if not package:
        return "Bitte gib einen Paketnamen an."
    try:
        r = requests.get(f"https://pypi.org/pypi/{quote(package)}/json", timeout=10)
        if r.status_code != 200:
            return f"Paket '{package}' nicht auf PyPI gefunden."
        d = r.json()
        info = d.get("info", {})
        ver = info.get("version", "?")
        desc = info.get("summary", "?")[:200]
        author = info.get("author", "?")
        url = info.get("home_page", "") or info.get("package_url", "")
        return f"PyPI: {package} v{ver}\n{desc}\nAutor: {author}\n{url}"
    except Exception as e:
        return f"Fehler: {e}"

def get_spaceflight_news(_=None):
    """Aktuelle Spaceflight-Nachrichten."""
    try:
        r = requests.get("https://api.spaceflightnewsapi.net/v4/articles/?limit=3", timeout=10)
        articles = r.json().get("results", [])
        if not articles:
            return "Keine Space-News gefunden."
        lines = ["Aktuelle Space-Nachrichten:"]
        for a in articles:
            lines.append(f"  - {a.get('title','?')} ({a.get('news_site','?')})")
            lines.append(f"    {a.get('url','')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Fehler: {e}"

def get_cocktail(name=None):
    """Zufälliger Cocktail oder Cocktail-Suche."""
    url = "https://www.thecocktaildb.com/api/json/v1/1/random.php"
    if name:
        url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={quote(name)}"
    try:
        r = requests.get(url, timeout=10)
        drinks = r.json().get("drinks", [])
        if not drinks:
            return f"Kein Cocktail '{name}' gefunden." if name else "Kein Cocktail gefunden."
        d = drinks[0]
        name = d.get("strDrink", "?")
        glass = d.get("strGlass", "?")
        instr = (d.get("strInstructions", "") or "")[:200]
        ingrs = []
        for i in range(1, 16):
            ing = d.get(f"strIngredient{i}")
            meas = d.get(f"strMeasure{i}")
            if ing:
                ingrs.append(f"{meas or ''} {ing}".strip())
        return f"Cocktail: {name}\nGlas: {glass}\nZutaten: {', '.join(ingrs)}\nZubereitung: {instr}"
    except Exception as e:
        return f"Fehler: {e}"

def get_trivia(_=None):
    """Zufällige Trivia-Frage."""
    try:
        r = requests.get("https://opentdb.com/api.php?amount=1", timeout=10)
        results = r.json().get("results", [])
        if not results:
            return "Keine Trivia-Frage gefunden."
        q = results[0]
        question = q.get("question", "?")
        difficulty = q.get("difficulty", "?")
        correct = q.get("correct_answer", "?")
        # HTML entities dekodieren
        question = html_to_text(question)
        correct = html_to_text(correct)
        return f"Trivia ({difficulty}):\n{question}\n\nAntwort: ||{correct}||"
    except Exception as e:
        return f"Fehler: {e}"

def get_jokeapi(category=None):
    """Witz von JokeAPI (Any, Programming, Misc, Dark, Pun)."""
    cat = (category or "Any").strip().title()
    try:
        r = requests.get(f"https://v2.jokeapi.dev/joke/{cat}?lang=de", timeout=10)
        data = r.json()
        if data.get("error"):
            return "Kein Witz gefunden."
        if data.get("type") == "twopart":
            return f"{data.get('setup','?')}\n{data.get('delivery','?')}"
        return data.get("joke", "?")
    except Exception as e:
        return f"Fehler: {e}"

def get_inspire_quote(_=None):
    """Inspirierendes Zitat (ZenQuotes)."""
    try:
        r = requests.get("https://zenquotes.io/api/random", timeout=10)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return f'"{data[0].get("q","?")}"\n— {data[0].get("a","?")}'
        return "Konnte kein Zitat laden."
    except Exception:
        return "Konnte kein Zitat laden."

def search_university(name):
    """Universitätssuche."""
    if not name:
        return "Bitte gib einen Universitätsnamen an."
    try:
        r = requests.get(f"https://universities.hipolabs.com/search?name={quote(name)}", timeout=10)
        unis = r.json()
        if not unis:
            return f"Keine Universität '{name}' gefunden."
        lines = [f"Universitäten zu '{name}':"]
        for u in unis[:5]:
            lines.append(f"  - {u.get('name','?')} ({u.get('country','?')})")
            domains = u.get("domains", [])
            if domains:
                lines.append(f"    Web: {domains[0]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Fehler: {e}"

def get_lyrics(argument):
    """Songtext-Suche (Artist - Title)."""
    if not argument or "-" not in argument:
        return "Bitte gib 'Artist - Title' an.\nBeispiel: TOOL: LYRICS Queen - Bohemian Rhapsody"
    parts = argument.split("-", 1)
    artist = parts[0].strip()
    title = parts[1].strip()
    try:
        r = requests.get(f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}", timeout=10)
        if r.status_code != 200:
            return f"Kein Text gefunden für '{artist} - {title}'."
        lyrics = r.json().get("lyrics", "")[:1500]
        return f"Song: {artist} - {title}\n\n{lyrics}"
    except Exception as e:
        return f"Fehler: {e}"

def get_bitcoin_price(_=None):
    """Aktueller Bitcoin-Preis (Blockchain.info)."""
    try:
        r = requests.get("https://blockchain.info/ticker", timeout=10)
        data = r.json()
        usd = data.get("USD", {}).get("15m", "?")
        eur = data.get("EUR", {}).get("15m", "?")
        gbp = data.get("GBP", {}).get("15m", "?")
        cny = data.get("CNY", {}).get("15m", "?")
        jpy = data.get("JPY", {}).get("15m", "?")
        return f"Bitcoin (BTC) Kurs:\nUSD: ${usd:,}\nEUR: €{eur:,}\nGBP: £{gbp:,}\nCNY: ¥{cny:,}\nJPY: ¥{jpy:,}"
    except Exception as e:
        return f"Fehler: {e}"


def handle_tool_command(command, argument):
    # Dispatch-Table: einfache Tools direct call
    _simple = {
        "TOOL: SEARCH": search_web, "TOOL: BROWSE": browse_url,
        "TOOL: PASSWORD": generate_password, "TOOL: FILESEARCH": search_files,
        "TOOL: DEEPRESEARCH": deep_research, "TOOL: RESEARCH": search_web,
        "TOOL: WEATHER": get_weather, "TOOL: SUMMARIZE": summarize_content,
        "TOOL: URLINFO": get_page_info, "TOOL: EXTRACTLINKS": extract_links_from_url,
        "TOOL: META": get_meta_tags, "TOOL: PAGEWORDS": count_page_words,
        "TOOL: FORMINFO": extract_forms_from_url, "TOOL: SUBMITFORM": submit_form_on_url,
        "TOOL: CLICK": click_on_url,
        "TOOL: TIME": get_current_time, "TOOL: DATE": lambda _: get_current_date(),
        "TOOL: UUID": lambda _: generate_uuid(), "TOOL: DICEROLL": roll_dice,
        "TOOL: BASE64": base64_tool, "TOOL: IPINFO": get_ip_info,
        "TOOL: CURRENCY": currency_convert, "TOOL: EMOJI": search_emoji,
        "TOOL: QRCODE": generate_qrcode, "TOOL: DEFINE": define_word,
        "TOOL: PING": ping_url, "TOOL: RANDOM": random_number,
        "TOOL: WORDCOUNT": word_count, "TOOL: FORMATJSON": format_json_text,
        "TOOL: UNITS": convert_units, "TOOL: TIMESTAMP": unix_timestamp,
        "TOOL: BIN": number_base, "TOOL: ASCII": ascii_codes,
        "TOOL: JOKE": lambda _: random_joke(), "TOOL: MEMORYTEST": memory_test,
        "TOOL: HASH": handle_hash,
        "TOOL: SHORTEN": handle_shorten,
        "TOOL: REMIND": handle_remind, "TOOL: CALC": handle_math, "TOOL: MATH": handle_math,
        "TOOL: LIST": handle_list_tool,
        # Neue Tools
        "TOOL: COUNTRY": get_country_info,
        "TOOL: DADJOKE": lambda _: get_dad_joke(),
        "TOOL: ADVICE": lambda _: get_advice(),
        "TOOL: QUOTE": lambda _: get_quote(),
        "TOOL: NUMBERS": get_number_fact,
        "TOOL: BORED": lambda _: get_bored_activity(),
        "TOOL: USELESSFACT": lambda _: get_useless_fact(),
        "TOOL: CATFACT": lambda _: get_cat_fact(),
        "TOOL: CHUCKNORRIS": lambda _: get_chuck_norris_joke(),
        "TOOL: COINGECKO": get_crypto_price,
        "TOOL: POKEMON": get_pokemon_info,
        "TOOL: SWAPI": get_swapi_info,
        "TOOL: TVSHOW": get_tv_show_info,
        "TOOL: GENDERIZE": get_gender_from_name,
        "TOOL: AGIFY": get_age_from_name,
        "TOOL: ISS": lambda _: get_iss_position(),
        "TOOL: MYIP": lambda _: get_my_ip(),
        "TOOL: RANDOMUSER": lambda _: get_random_user(),
        "TOOL: EXCUSE": lambda _: get_excuse(),
        "TOOL: EARTHQUAKE": lambda _: get_earthquake_info(),
        "TOOL: DICTIONARY": get_dictionary_en,
        # Neue Tools v2
        "TOOL: DOG": get_dog_image,
        "TOOL: CAT": lambda _: get_cat_image(),
        "TOOL: FOX": lambda _: get_fox_image(),
        "TOOL: RIDDLE": lambda _: get_riddle(),
        "TOOL: KANYE": lambda _: get_kanye_quote(),
        "TOOL: GITHUB": get_github_user,
        "TOOL: PYPISEARCH": get_pypi_package,
        "TOOL: SPACEFLIGHT": lambda _: get_spaceflight_news(),
        "TOOL: COCKTAIL": get_cocktail,
        "TOOL: TRIVIA": lambda _: get_trivia(),
        "TOOL: JOKEAPI": get_jokeapi,
        "TOOL: INSPIRE": lambda _: get_inspire_quote(),
        "TOOL: UNIVERSITY": search_university,
        "TOOL: LYRICS": get_lyrics,
        "TOOL: BITCOIN": lambda _: get_bitcoin_price(),
    }
    if command in _simple:
        return _simple[command](argument)

    # Tools die ihre Argumente wrappen
    if command in ("TOOL: NEWS", "TOOL: NEWSFEED"):
        return search_web(f"Aktuelle Nachrichten {argument}")
    if command == "TOOL: RECIPE":
        return search_web(f"Rezept {argument}")
    if command == "TOOL: PRICE":
        return search_web(f"Preisvergleich {argument}")
    if command == "TOOL: WIKI":
        return browse_url(f"https://de.wikipedia.org/wiki/{quote(argument.replace(' ', '_'))}")

    if command == "TOOL: TRANSLATE":
        parts = argument.split(":", 1)
        lang = parts[0].strip() if len(parts) == 2 and re.match(r"^[a-zA-Z\-]{2,}(->([a-zA-Z\-]{2,}))?$", parts[0].strip()) else None
        return translate_text(parts[1].strip() if lang else argument, lang)

    # Tools die ihr Argument ignorieren
    if command == "TOOL: MEMORY":
        return show_memory_content(None)
    if command in ("TOOL: TOOLS", "TOOL: HELP"):
        return TOOL_HELP_TEXT

    return f"Unbekanntes Tool: {command}"


def translate_text(text, lang_part=None):
    if not text:
        return "Bitte gib einen Text zum Übersetzen an."
    target = "de"
    source = "auto"
    if lang_part:
        if "->" in lang_part:
            src, tgt = lang_part.split("->", 1)
            source = src.strip()
            target = tgt.strip()
        else:
            target = lang_part.strip()

    # Mehrere Übersetzungs-Backends (Fallback-Kette)
    backends = [
        # 1. LibreTranslate (öffentliche Instanz)
        ("libre", lambda: _translate_libre(text, source, target)),
        # 2. MyMemory (mit Rate-Limit)
        ("mymemory", lambda: _translate_mymemory(text, source, target)),
    ]

    errors = []
    for name, fn in backends:
        try:
            result = fn()
            if result:
                return result
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

    return f"❌ Übersetzung fehlgeschlagen. {'; '.join(errors)}"


def _translate_libre(text, source, target):
    """LibreTranslate (öffentliche API)."""
    for host in ("https://libretranslate.de", "https://translate.argosopentech.com"):
        try:
            resp = requests.post(
                f"{host}/translate",
                json={"q": text, "source": source, "target": target, "format": "text"},
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and data.get("translatedText"):
                    return data["translatedText"]
        except Exception:
            continue
    return None


def _translate_mymemory(text, source, target):
    """MyMemory Translated (free tier, 1000/Tag/IP)."""
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{source}|{target}", "de": "buno23@web.de"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("responseStatus") == 200:
                return data.get("responseData", {}).get("translatedText", "")
    except Exception:
        pass
    return None


def remove_markdown_code_blocks(text):
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        return "\n".join(lines[1:-1])
    return text


def get_user_memory_paths(author):
    project_root = PROJECT_ROOT
    memory_dir = os.path.join(project_root, "Agent", "Memorys")
    os.makedirs(memory_dir, exist_ok=True)

    user_id = getattr(author, "id", None)
    user_name = getattr(author, "name", None) or str(author)
    safe_name = re.sub(r"[^\w\-_.]", "_", user_name)

    memory_file = os.path.join(memory_dir, f"user_{user_id}_memory.txt") if user_id else os.path.join(memory_dir, f"user_{safe_name}_memory.txt")
    history_file = os.path.join(memory_dir, f"user_{user_id}_chat_history.txt") if user_id else os.path.join(memory_dir, f"user_{safe_name}_chat_history.txt")

    if user_id:
        for filename in os.listdir(memory_dir):
            filepath = os.path.join(memory_dir, filename)
            if not os.path.isfile(filepath):
                continue
            if filename.endswith("_memory.txt") and (filename.startswith(f"user_{user_id}_") or filename.startswith(f"user_{safe_name}_")):
                memory_file = filepath
            elif filename.endswith("_chat_history.txt") and (filename.startswith(f"user_{user_id}_") or filename.startswith(f"user_{safe_name}_")):
                history_file = filepath

    for path in (memory_file, history_file):
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    # Ensure memory contains a directive so the AI only responds when asked
    directive = (
        "MEMORY_INSTRUCTION: Reagiere nur auf direkte Nachfragen zu diesem Memory. "
        "Wenn mit dem neuen Tool nachgefragt wird, füge auch die alten Chatverläufe hinzu.\n"
    )
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.startswith("MEMORY_INSTRUCTION:"):
            with open(memory_file, "w", encoding="utf-8") as f:
                f.write(directive + content)
    except Exception:
        # If anything goes wrong, ignore and continue
        pass

    return memory_file, history_file


def get_memory_and_history_contents(author, include_history=False):
    """Return the memory and optionally chat history contents for an author.

    The memory file always includes a directive instructing the AI to only
    react to queries about the memory. If include_history is True, the chat
    history contents are also returned.
    """
    memory_file, history_file = get_user_memory_paths(author)
    memory_text = ""
    history_text = ""
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            memory_text = f.read()
    except Exception:
        memory_text = ""
    if include_history:
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_text = f.read()
        except Exception:
            history_text = ""
    return memory_text, history_text


def sanitize_answer(answer):
    answer = answer.strip()
    if not answer:
        return "Keine Antwort erhalten."
    answer = re.sub(r"(?im)^(?:user|root)@terminal:~\$\s*", "", answer)
    command, _ = extract_tool_command(answer)
    if command:
        return "Entschuldigung, ich konnte das Tool nicht verwenden."
    return answer


def tool_output_indicates_missing_params(tool_output, tool_name):
    """Prüft ob die Tool-Ausgabe auf fehlende Parameter hinweist."""
    if not tool_output:
        return True
    missing_indicators = [
        "Bitte gib",
        "Bitte eine",
        "Bitte den",
        "Bitte die",
        "Bitte ein",
        "Bitte einen",
        "Bitte das",
        "Keine Tool-Anweisung",
        "Unbekanntes Tool",
        "gib eine",
        "gib einen",
        "gib ein",
        "gib den",
        "gib die",
        "Kein",
    ]
    lower = tool_output.lower()
    for indicator in missing_indicators:
        if indicator.lower() in lower and "erfolgreich" not in lower:
            req_type, param_desc = get_tool_param_requirement(tool_name)
            if req_type == "required":
                return True
    return False


async def run_sync(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def _progress(msg="Denke nach"):
    print(f"\r{msg}...  ", end="", flush=True)


def _call_llm(prompt, model="gemma-4-31b-it", retries=2):
    """LLM-Aufruf mit Retry und Progress-Indikator."""
    _progress()
    for attempt in range(retries):
        try:
            r = client.responses.create(model=model, input=prompt)
            print("\r" + " " * 40 + "\r", end="", flush=True)
            return r
        except Exception as e:
            if attempt == retries - 1:
                print("\r" + " " * 40 + "\r", end="", flush=True)
                raise
            _progress(f"Wiederholung {attempt+2}")
    return None  # unreachable


def get_response_text(response):
    if response is None:
        return ""
    if hasattr(response, "output_text"):
        return response.output_text or ""
    if hasattr(response, "output"):
        output = response.output
        if isinstance(output, list):
            texts = []
            for item in output:
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                texts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                texts.append(block)
                    elif isinstance(content, str):
                        texts.append(content)
                elif isinstance(item, str):
                    texts.append(item)
            if texts:
                return "\n".join(texts)
        elif isinstance(output, dict):
            content = output.get("content")
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        texts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        texts.append(block)
                if texts:
                    return "\n".join(texts)
    return str(response)


# API-Einstellungen


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing API key. Set OPENAI_API_KEY environment variable.")

client = OpenAI(
    api_key=api_key,
    base_url="https://llm.services.digital-hub.sh/v1",
    timeout=30.0,
    max_retries=0,
)





# Standardwerte für Python-Modus


DEFAULT_INSTRUCTIONS = (
    "You are a Python programmer who only answers with Python code. "
    "Do not include explanations or text outside the code."
)

DEFAULT_PROMPT = (
    "Write a simple Python script."
)


def python_mode():
    print("\n=== PYTHON-MODUS ===")
    print("Tippe 'exit' oder 'menu' um zum Hauptmenü zurückzukehren.\n")
    
    project_root = PROJECT_ROOT
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    
    while True:
        user_input = input("Prompt: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "ende", "menu", "hauptmenü", "zurück", "back"):
            print("Beende Python-Modus.")
            break
        try:
            response = client.responses.create(
                model="gemma-4-31b-it",
                instructions=DEFAULT_INSTRUCTIONS,
                input=user_input,
            )
            result = remove_markdown_code_blocks(get_response_text(response).strip())
            
            # Dateiname aus Prompt ableiten oder generieren
            safe_name = re.sub(r'[^\w\-]', '_', user_input[:20].strip())
            if not safe_name:
                safe_name = "generated"
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            filename = f"{safe_name}_{timestamp}.py"
            filepath = os.path.join(agent_dir, filename)
            
            # Code in Datei schreiben
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result)
            
            print(f"\n--- Gespeichert als: {filename} ---\n")
            print(result)
            print(f"\n--- Ende von {filename} ---\n")
        except Exception as e:
            print("Fehler:", e)


# Chat-Modus


def chat_mode():
    print("\n==============================")
    print("        CHAT-MODUS")
    print("==============================")
    print("Tippe 'exit' oder 'menu' um zum Hauptmenü zurückzukehren.\n")

    project_root = PROJECT_ROOT
    memory_dir = os.path.join(project_root, "Agent", "Memorys")
    os.makedirs(memory_dir, exist_ok=True)

    memory_file = os.path.join(memory_dir, "terminal_memory.txt")
    history_file = os.path.join(memory_dir, "terminal_chat_history.txt")
    if not os.path.exists(memory_file):
        open(memory_file, "w", encoding="utf-8").close()

    memory = ""
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            memory = f.read()
    chat_history = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            chat_history = [line.strip() for line in f if line.strip()]

    def _save():
        with open(history_file, "w", encoding="utf-8") as f:
            f.write("\n".join(chat_history[-30:]) + "\n")
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(memory)

    def _cleanup(sig=None, frame=None):
        _save()
        print("\n\nChat gespeichert. Rückkehr zum Menü.")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _cleanup)

    msg_count = 0
    while True:
        try:
            user_input = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            _cleanup()

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "ende", "menu", "hauptmenü", "zurück", "back"]:
            _save()
            print("\nZurück zum Hauptmenü.\n")
            break

        shortcut_command, shortcut_arg = parse_tool_shortcut(user_input)
        if shortcut_command:
            print(f"\nTool-Ausgabe:\n{run_tool_command(shortcut_command, shortcut_arg)}\n")
            chat_history.append(f"User: {user_input}")
            continue

        msg_count += 1
        try:
            _progress()
            answer, new_memory, updated_history = process_message(
                user_input, chat_history, memory, save=False
            )
            print("\r" + " " * 40 + "\r", end="", flush=True)
            chat_history = updated_history
            print(f"\nKI: {answer}\n")

            if msg_count % 5 == 0:
                memory = new_memory
                _save()
            else:
                with open(history_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(chat_history[-30:]) + "\n")
        except Exception as e:
            print("\r" + " " * 40 + "\r", end="", flush=True)
            print(f"Fehler: {e}")


# Hauptmenü

discord_intents = discord.Intents.default()
discord_intents.messages = True
discord_intents.dm_messages = True
discord_intents.message_content = True

discord_client = None

def create_discord_client():
    client = discord.Client(intents=discord_intents)

    @client.event
    async def on_ready():
        print(f"Discord-Bot gestartet als {client.user}.")

    @client.event
    async def on_disconnect():
        print("Discord-Bot gestoppt.")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            await handle_discord_dm(message)

    return client


async def discord_send_long(channel, text, max_len=1990):
    """Sendet lange Nachrichten in mehreren Teilen über Discord."""
    if not text:
        await channel.send("(leere Antwort)")
        return
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at < max_len // 2:
            split_at = text.rfind(" ", 0, max_len)
        if split_at < max_len // 2:
            split_at = max_len
        await channel.send(text[:split_at])
        text = text[split_at:].strip()
    if text:
        await channel.send(text)


async def handle_discord_dm(message):
    user_input = message.content.strip()
    if not user_input:
        return

    if user_input.lower() in ("!stop", "!shutdown", "!quit", "!exit"):
        await message.channel.send("Bot wird beendet.")
        if discord_client:
            await discord_client.close()
        return

    if user_input.lower().startswith("!python "):
        prompt = user_input[len("!python "):].strip()
        if not prompt:
            await message.channel.send("Bitte gib einen Prompt nach `!python` ein.")
            return
        try:
            response = await run_sync(
                client.responses.create,
                model="gemma-4-31b-it",
                instructions=DEFAULT_INSTRUCTIONS,
                input=prompt,
            )
            result = remove_markdown_code_blocks(get_response_text(response).strip())
            if len(result) + 10 < 2000:
                await message.channel.send(f"```python\n{result}\n```")
            else:
                await message.channel.send(result[:1990])
        except Exception as e:
            await message.channel.send(f"Fehler: {e}")
        return

    shortcut_command, shortcut_arg = parse_tool_shortcut(user_input)
    if shortcut_command:
        tool_output = run_tool_command(shortcut_command, shortcut_arg)
        await discord_send_long(message.channel, tool_output)
        return

    project_root = PROJECT_ROOT
    memory_dir = os.path.join(project_root, "Agent", "Memorys")
    os.makedirs(memory_dir, exist_ok=True)

    memory_file = os.path.join(memory_dir, f"user_{message.author.id}_memory.txt")
    history_file = os.path.join(memory_dir, f"user_{message.author.id}_chat_history.txt")

    if not os.path.exists(memory_file):
        open(memory_file, "w", encoding="utf-8").close()

    chat_history = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            chat_history = [line.strip() for line in f if line.strip()]

    chat_history.append(f"User: {user_input}")

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            memory = f.read()

        # Prompt mit Persönlichkeit
        history_slice = chat_history[-20:] if len(chat_history) > 20 else chat_history
        prompt = f"""{SYSTEM_PROMPT}

Memory:
{memory}

Verlauf:
{chr(10).join(history_slice)}

{user_input}
"""
        response = await run_sync(client.responses.create, model="gemma-4-31b-it", input=prompt)
        answer = get_response_text(response).strip()

        # Tool-Loop: max 2 Durchläufe, alle Befehle aus einer Antwort verarbeiten
        for _ in range(2):
            commands = extract_all_tool_commands(answer)
            if not commands:
                break

            # Alle gefundenen Befehle nacheinander ausführen
            all_outputs = []
            for cmd, arg in commands:
                # Zuerst KI nach der genauen Parameter-Bestätigung fragen
                confirm_prompt = f"""The tool {cmd} was requested with the parameter: "{arg}".

Confirm what exact parameter/attribute should be passed to this tool.
If the parameter is correct as-is, respond with ONLY the confirmed value.
If it needs refinement or more detail, provide the corrected parameter only.
No explanations, no extra text."""
                confirm_resp = await run_sync(
                    client.responses.create, model="gemma-4-31b-it",
                    input=confirm_prompt
                )
                confirmed_arg = get_response_text(confirm_resp).strip()

                out = handle_tool_command(cmd, confirmed_arg)
                if out.strip():
                    all_outputs.append(f"[{cmd}] {out}")

            tool_output = "\n".join(all_outputs) if all_outputs else "(keine Ausgabe)"
            chat_history.append(f"Assistant: {answer}")
            chat_history.append(f"Tool: {tool_output}")
            if not tool_output.strip() or tool_output.startswith("Fehler"):
                break

            response = await run_sync(
                client.responses.create, model="gemma-4-31b-it",
                input=f"""Tool-Ergebnis verarbeiten:
{tool_output}

Bisheriger Verlauf:
{chr(10).join(chat_history)}

Erstelle eine praezise Antwort basierend auf dem Tool-Ergebnis. Verifiziere wenn noetig.
"""
            )
            answer = get_response_text(response).strip()

        await discord_send_long(message.channel, answer)
        chat_history.append(f"Assistant: {answer}")
        if len(chat_history) > 30:
            chat_history = chat_history[-30:]
        with open(history_file, "w", encoding="utf-8") as f:
            f.write("\n".join(chat_history) + "\n")

        memory_update = await run_sync(
            client.responses.create, model="gemma-4-31b-it",
            input=f"""Aktualisiere Memory (Datum immer speichern):
Aktuelles Datum: {datetime.datetime.now().strftime('%d.%m.%Y')}
Alte Memory: {memory}
Verlauf: {chr(10).join(chat_history)}
Neue Memory (mit Datum):
"""
        )
        new_memory = get_response_text(memory_update).strip()
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(new_memory)

    except Exception as e:
        await message.channel.send(f"Fehler: {e}")


def process_message(user_input, chat_history=None, memory=None, save=True):
    """Verarbeitet eine Nutzereingabe mit Tool-Loop und Memory-Update.

    Args:
        user_input: Der eingegebene Text des Nutzers
        chat_history: Optional. Liste mit Verlauf (None = aus Datei laden)
        memory: Optional. Memory-String (None = aus Datei laden)
        save: Ob Memory + History gespeichert werden sollen

    Returns:
        tuple: (answer, new_memory, updated_history)
    """
    project_root = PROJECT_ROOT
    memory_dir = os.path.join(project_root, "Agent", "Memorys")
    os.makedirs(memory_dir, exist_ok=True)

    memory_file = os.path.join(memory_dir, "terminal_memory.txt")
    history_file = os.path.join(memory_dir, "terminal_chat_history.txt")

    if chat_history is None:
        chat_history = []
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                chat_history = [line.strip() for line in f if line.strip()]

    if memory is None:
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                memory = f.read()
        else:
            memory = ""

    if not user_input.strip():
        return "Bitte gib eine Nachricht ein.", memory, chat_history

    chat_history = list(chat_history)
    chat_history.append(f"User: {user_input}")

    # Prompt (process_message)
    history_slice = chat_history[-20:] if len(chat_history) > 20 else chat_history
    prompt = f"""{SYSTEM_PROMPT}

Memory:
{memory}

Verlauf:
{chr(10).join(history_slice)}

{user_input}
"""
    response = _call_llm(prompt)
    answer = get_response_text(response).strip()

    # Tool-Loop: max 2 Durchläufe, alle Befehle aus einer Antwort verarbeiten
    for _ in range(2):
        commands = extract_all_tool_commands(answer)
        if not commands:
            break

        # Alle gefundenen Befehle nacheinander ausführen
        all_outputs = []
        for cmd, arg in commands:
            # Zuerst KI nach der genauen Parameter-Bestätigung fragen
            confirm_prompt = f"""The tool {cmd} was requested with the parameter: "{arg}".

Confirm what exact parameter/attribute should be passed to this tool.
If the parameter is correct as-is, respond with ONLY the confirmed value.
If it needs refinement or more detail, provide the corrected parameter only.
No explanations, no extra text."""
            confirm_resp = _call_llm(confirm_prompt)
            confirmed_arg = get_response_text(confirm_resp).strip()

            out = handle_tool_command(cmd, confirmed_arg)
            if out.strip():
                all_outputs.append(f"[{cmd}] {out}")
            if tool_output_indicates_missing_params(out, cmd.replace("TOOL: ", "")):
                req_type, param_desc = get_tool_param_requirement(cmd.replace("TOOL: ", ""))
                if param_desc:
                    all_outputs.append(f"[!] Fehlende Parameter für {cmd}: {param_desc}.")

        tool_output = "\n".join(all_outputs) if all_outputs else "(keine Ausgabe)"
        chat_history.append(f"Assistant: {answer}")
        chat_history.append(f"Tool: {tool_output}")

        if not tool_output.strip() or tool_output.startswith("Fehler"):
            break

        response = _call_llm(f"""Tool-Ergebnis verarbeiten:
{tool_output}

Bisheriger Verlauf:
{chr(10).join(chat_history)}

Erstelle eine praezise Antwort. Verifiziere wenn noetig.
""")
        answer = get_response_text(response).strip()

    answer = sanitize_answer(answer)
    chat_history.append(f"Assistant: {answer}")

    # Memory-Update
    memory_update = _call_llm(f"""Aktualisiere Memory (Datum immer speichern):
Aktuelles Datum: {datetime.datetime.now().strftime('%d.%m.%Y')}
Alte Memory: {memory}
Verlauf: {chr(10).join(chat_history)}
Neue Memory (mit Datum):
""")
    new_memory = get_response_text(memory_update).strip()

    if save:
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(new_memory)
        if len(chat_history) > 30:
            chat_history = chat_history[-30:]
        with open(history_file, "w", encoding="utf-8") as f:
            f.write("\n".join(chat_history) + "\n")

    return answer, new_memory, chat_history


if __name__ == "__main__":
    discord_token = os.getenv("DISCORD_TOKEN")
    print("=" * 46)
    print("         KI TERMINAL TOOL")
    print("=" * 46)

    # Cross-Plattform Single-Key-Eingabe
    def _read_key():
        """Liest einen Tastendruck ohne Enter (Windows & Unix)."""
        import sys as _sys
        if _sys.platform == "win32":
            import msvcrt
            while True:
                k = msvcrt.getch()
                if k in (b"1", b"2", b"3", b"4", b"5"):
                    return k.decode()
                if k == b"\x03":
                    raise KeyboardInterrupt
        else:
            import tty, termios
            fd = _sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    k = _sys.stdin.read(1)
                    if k in "12345":
                        return k
                    if k == "\x03":
                        raise KeyboardInterrupt
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    while True:
        print("\n" + "-" * 46)
        print("  HAUPTMENU (Zahl drucken = sofort)")
        print("-" * 46)
        print("  1  Chat-Modus")
        print("  2  Python-Code generieren")
        if discord_token:
            print("  3  Discord-Bot starten")
        print("  4  GUI-Modus")
        print("  5  Beenden")
        print("-" * 46, end=" ", flush=True)
        mode = _read_key()
        print(mode)

        if mode == "1":
            chat_mode()
        elif mode == "2":
            python_mode()
        elif mode == "3" and discord_token:
            print("\nStarte den Discord-Bot...")
            print("  Zum Stoppen: !stop in Discord schreiben")
            print("  Oder Strg+C im Terminal drücken\n")
            discord_client = create_discord_client()
            try:
                discord_client.run(discord_token)
            except KeyboardInterrupt:
                print("\nBot wird gestoppt (Strg+C)...")
            except Exception as e:
                print(f"Discord-Fehler: {e}")
            print("\nBot gestoppt. Rückkehr zum Hauptmenü.")
            continue
        elif mode == "4":
            print("\nStarte GUI-Modus...")
            try:
                from gui import AgentGUI
                app = AgentGUI()
                app.mainloop()
            except ImportError as e:
                print(f"Fehler beim Laden des GUI: {e}")
                print("Stelle sicher dass customtkinter installiert ist: pip install customtkinter")
            except Exception as e:
                print(f"GUI-Fehler: {e}")
            print("\nGUI geschlossen. Rückkehr zum Hauptmenü.")
            continue
        elif mode in ("3", "5", "exit", "quit", "ende") or (mode in ("3", "5") and not discord_token):
            print("Programm beendet.")
            break
        else:
            print("Ungültige Auswahl.")