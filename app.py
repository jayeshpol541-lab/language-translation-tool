import os
import sqlite3
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "translations.db")
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

LANGUAGES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "pa": "Punjabi", "ur": "Urdu", "es": "Spanish",
    "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese",
    "ru": "Russian", "ja": "Japanese", "ko": "Korean", "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic", "tr": "Turkish", "th": "Thai", "vi": "Vietnamese",
    "id": "Indonesian", "nl": "Dutch", "pl": "Polish", "uk": "Ukrainian"
}

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def translate_with_mymemory(text, source, target):
    # MyMemory's documented q parameter has a maximum of 500 bytes.
    # Split long input into manageable chunks while preserving paragraph breaks.
    chunks = []
    remaining = text.strip()
    while remaining:
        # MyMemory documents a 500-byte limit; leave a little safety margin.
        piece = ""
        for character in remaining:
            if len((piece + character).encode("utf-8")) > 450:
                break
            piece += character
        if not piece:
            raise ValueError("A character in the input is too large to process.")
        if len(piece) < len(remaining):
            split_at = max(piece.rfind(". "), piece.rfind("? "), piece.rfind("! "),
                           piece.rfind("\\n"), piece.rfind(" "))
            if split_at > 100:
                piece = piece[:split_at + 1]
        chunks.append(piece)
        remaining = remaining[len(piece):].lstrip()

    translated_parts = []
    for chunk in chunks:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": chunk, "langpair": f"{source}|{target}", "mt": "1"},
            timeout=25
        )
        response.raise_for_status()
        data = response.json()
        if data.get("responseStatus") != 200:
            message = data.get("responseDetails") or "The translation service could not process this text."
            raise RuntimeError(message)
        translated = data.get("responseData", {}).get("translatedText", "")
        if not translated:
            raise RuntimeError("The translation service returned an empty result.")
        translated_parts.append(translated)

    return " ".join(translated_parts)

@app.route("/")
def home():
    return render_template("index.html", languages=LANGUAGES)

@app.route("/api/translate", methods=["POST"])
def translate():
    payload = request.get_json(silent=True) or {}
    original_text = (payload.get("text") or "").strip()
    source = payload.get("source") or ""
    target = payload.get("target") or ""

    if not original_text:
        return jsonify({"error": "Please enter text to translate."}), 400
    if len(original_text) > 5000:
        return jsonify({"error": "Please keep the text under 5,000 characters."}), 400
    if source not in LANGUAGES or target not in LANGUAGES:
        return jsonify({"error": "Please select valid source and target languages."}), 400
    if source == target:
        return jsonify({"error": "Source and target languages must be different."}), 400

    try:
        translated_text = translate_with_mymemory(original_text, source, target)
        created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO translations
                (source_language, target_language, original_text, translated_text, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source, target, original_text, translated_text, created_at))
            translation_id = cursor.lastrowid

        return jsonify({
            "id": translation_id,
            "translated_text": translated_text,
            "source_language": LANGUAGES[source],
            "target_language": LANGUAGES[target],
            "created_at": created_at
        })
    except requests.Timeout:
        return jsonify({"error": "Translation service timed out. Please try again."}), 504
    except requests.RequestException:
        return jsonify({"error": "Could not connect to the translation service. Check your internet connection."}), 502
    except (RuntimeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception:
        app.logger.exception("Unexpected translation error")
        return jsonify({"error": "An unexpected server error occurred."}), 500

@app.route("/api/history", methods=["GET"])
def history():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, source_language, target_language, original_text,
                   translated_text, created_at
            FROM translations ORDER BY id DESC LIMIT 20
        """).fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/history/<int:translation_id>", methods=["DELETE"])
def delete_history_item(translation_id):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM translations WHERE id = ?", (translation_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "History item not found."}), 404
    return jsonify({"message": "History item deleted."})

@app.route("/api/history", methods=["DELETE"])
def clear_history():
    with get_db() as conn:
        conn.execute("DELETE FROM translations")
    return jsonify({"message": "Translation history cleared."})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Language Translation Tool"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
