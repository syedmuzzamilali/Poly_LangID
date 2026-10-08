import os
import sys
import time
import json
from flask import Flask, render_template, request, jsonify

# Add parent directory to sys.path to import polylid module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import polylid

app = Flask(__name__, template_folder="templates", static_folder="static")

# Language Metadata for all 65 common languages supported across FastText, GlotLID, and Lingua
LANG_META = {
    # Latin Script
    "af": {"name": "Afrikaans", "script": "Latin", "color": "#047857"},
    "az": {"name": "Azerbaijani", "script": "Latin", "color": "#0284c7"},
    "bs": {"name": "Bosnian", "script": "Latin", "color": "#4f46e5"},
    "ca": {"name": "Catalan", "script": "Latin", "color": "#d97706"},
    "cs": {"name": "Czech", "script": "Latin", "color": "#ea580c"},
    "cy": {"name": "Welsh", "script": "Latin", "color": "#16a34a"},
    "da": {"name": "Danish", "script": "Latin", "color": "#dc2626"},
    "de": {"name": "German", "script": "Latin", "color": "#ea580c"},
    "en": {"name": "English", "script": "Latin", "color": "#2563eb"},
    "eo": {"name": "Esperanto", "script": "Latin", "color": "#059669"},
    "es": {"name": "Spanish", "script": "Latin", "color": "#dc2626"},
    "et": {"name": "Estonian", "script": "Latin", "color": "#0284c7"},
    "eu": {"name": "Basque", "script": "Latin", "color": "#ca8a04"},
    "fi": {"name": "Finnish", "script": "Latin", "color": "#2563eb"},
    "fr": {"name": "French", "script": "Latin", "color": "#7c3aed"},
    "ga": {"name": "Irish", "script": "Latin", "color": "#15803d"},
    "hr": {"name": "Croatian", "script": "Latin", "color": "#be123c"},
    "hu": {"name": "Hungarian", "script": "Latin", "color": "#047857"},
    "id": {"name": "Indonesian", "script": "Latin", "color": "#4f46e5"},
    "is": {"name": "Icelandic", "script": "Latin", "color": "#1d4ed8"},
    "it": {"name": "Italian", "script": "Latin", "color": "#16a34a"},
    "la": {"name": "Latin", "script": "Latin", "color": "#64748b"},
    "lt": {"name": "Lithuanian", "script": "Latin", "color": "#d97706"},
    "lv": {"name": "Latvian", "script": "Latin", "color": "#b91c1c"},
    "ms": {"name": "Malay", "script": "Latin", "color": "#0891b2"},
    "nl": {"name": "Dutch", "script": "Latin", "color": "#f97316"},
    "nn": {"name": "Norwegian Nynorsk", "script": "Latin", "color": "#0284c7"},
    "pl": {"name": "Polish", "script": "Latin", "color": "#be123c"},
    "pt": {"name": "Portuguese", "script": "Latin", "color": "#047857"},
    "ro": {"name": "Romanian", "script": "Latin", "color": "#ca8a04"},
    "sk": {"name": "Slovak", "script": "Latin", "color": "#e11d48"},
    "sl": {"name": "Slovene", "script": "Latin", "color": "#4f46e5"},
    "so": {"name": "Somali", "script": "Latin", "color": "#0891b2"},
    "sq": {"name": "Albanian", "script": "Latin", "color": "#b91c1c"},
    "sv": {"name": "Swedish", "script": "Latin", "color": "#2563eb"},
    "sw": {"name": "Swahili", "script": "Latin", "color": "#059669"},
    "tl": {"name": "Tagalog", "script": "Latin", "color": "#ea580c"},
    "tr": {"name": "Turkish", "script": "Latin", "color": "#e11d48"},
    "vi": {"name": "Vietnamese", "script": "Latin", "color": "#d97706"},
    "yo": {"name": "Yoruba", "script": "Latin", "color": "#15803d"},
    # Cyrillic Script
    "be": {"name": "Belarusian", "script": "Cyrillic", "color": "#0284c7"},
    "kk": {"name": "Kazakh", "script": "Cyrillic", "color": "#0891b2"},
    "mk": {"name": "Macedonian", "script": "Cyrillic", "color": "#ca8a04"},
    "mn": {"name": "Mongolian", "script": "Cyrillic", "color": "#1d4ed8"},
    "ru": {"name": "Russian", "script": "Cyrillic", "color": "#1d4ed8"},
    "sr": {"name": "Serbian", "script": "Cyrillic", "color": "#7c3aed"},
    "uk": {"name": "Ukrainian", "script": "Cyrillic", "color": "#0284c7"},
    # Arabic / Perso-Arabic Script
    "ar": {"name": "Arabic", "script": "Arabic", "color": "#059669"},
    "fa": {"name": "Persian", "script": "Arabic", "color": "#0d9488"},
    "ur": {"name": "Urdu", "script": "Arabic", "color": "#15803d"},
    # Indic / South Asian Scripts
    "bn": {"name": "Bengali", "script": "Bengali", "color": "#d97706"},
    "gu": {"name": "Gujarati", "script": "Gujarati", "color": "#0d9488"},
    "hi": {"name": "Hindi", "script": "Devanagari", "color": "#e11d48"},
    "mr": {"name": "Marathi", "script": "Devanagari", "color": "#ea580c"},
    "pa": {"name": "Punjabi", "script": "Gurmukhi", "color": "#f59e0b"},
    "ta": {"name": "Tamil", "script": "Tamil", "color": "#b91c1c"},
    "te": {"name": "Telugu", "script": "Telugu", "color": "#6d28d9"},
    # East & Southeast Asian Scripts
    "zh": {"name": "Chinese", "script": "Han", "color": "#b91c1c"},
    "ja": {"name": "Japanese", "script": "Kana/Kanji", "color": "#db2777"},
    "ko": {"name": "Korean", "script": "Hangul", "color": "#9333ea"},
    "th": {"name": "Thai", "script": "Thai", "color": "#c026d3"},
    # Hellenic, Caucasian, Semitic Scripts
    "el": {"name": "Greek", "script": "Greek", "color": "#2563eb"},
    "he": {"name": "Hebrew", "script": "Hebrew", "color": "#4f46e5"},
    "hy": {"name": "Armenian", "script": "Armenian", "color": "#ea580c"},
    "ka": {"name": "Georgian", "script": "Georgian", "color": "#7c3aed"}
}

# Global singleton detector
print("Initializing PolyLID Framework for Academic Workbench...")
start_init = time.time()
detector = polylid.get_detector()
init_time = (time.time() - start_init) * 1000
print(f"PolyLID Framework initialized successfully in {init_time:.2f} ms.")

@app.route("/")
def index():
    return render_template("index.html", lang_meta=LANG_META)

@app.route("/api/identify", methods=["POST"])
def identify():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
        
    text = data.get("text", "").strip()
    allowed_input = data.get("allowed_langs", "")
    
    allowed = None
    if allowed_input and isinstance(allowed_input, str) and allowed_input.strip() != "all":
        allowed = [lang.strip().lower() for lang in allowed_input.split(",") if lang.strip()]
    elif isinstance(allowed_input, list) and len(allowed_input) > 0:
        allowed = [str(lang).strip().lower() for lang in allowed_input if str(lang).strip()]
        
    if not text:
        return jsonify({
            "spans": [],
            "tokens": [],
            "latency_ms": 0.0,
            "metrics": {
                "total_tokens": 0,
                "total_spans": 0,
                "latency_ms": 0.0,
                "languages": {},
                "stages": {},
                "models": {}
            }
        })
        
    start_t = time.time()
    active_det = polylid.get_detector()
    spans = active_det.detect_languages(text, allowed_langs=allowed)
    tokens = active_det.identify_to_dict(text, allowed_langs=allowed)
    latency = (time.time() - start_t) * 1000.0
    
    # Calculate metrics & enrich tokens
    stages_count = {}
    models_count = {}
    lang_char_count = {}
    total_chars = 0

    for t in tokens:
        lab = t.get("label", "en")
        tok_len = len(t.get("token", ""))
        total_chars += tok_len
        lang_char_count[lab] = lang_char_count.get(lab, 0) + tok_len

        meta = LANG_META.get(lab, {"name": lab.upper(), "script": t.get("script", "Unknown"), "color": "#64748b"})
        t["lang_name"] = meta["name"]
        t["lang_color"] = meta["color"]

        dec = str(t.get("decided_by", "Unknown"))
        reason = str(t.get("reason", ""))
        models_count[dec] = models_count.get(dec, 0) + 1
        
        if "LocalContext" in dec or "Local/Dissenting" in reason or "ContextRefinement" in dec:
            stage = "Local Context"
        elif "Consensus" in reason or "+" in dec or "Unanimous" in reason:
            stage = "Consensus"
        else:
            stage = "Evidence Comparison"
        stages_count[stage] = stages_count.get(stage, 0) + 1

    # Format spans with metadata
    enriched_spans = []
    for span_text, lang in spans:
        meta = LANG_META.get(lang, {"name": lang.upper(), "script": "Unknown", "color": "#64748b"})
        enriched_spans.append({
            "text": span_text,
            "lang": lang,
            "name": meta["name"],
            "color": meta["color"]
        })

    # Language percentage summary
    lang_summary = []
    for lang, count in sorted(lang_char_count.items(), key=lambda x: x[1], reverse=True):
        meta = LANG_META.get(lang, {"name": lang.upper(), "color": "#64748b"})
        pct = round((count / max(1, total_chars)) * 100, 1)
        lang_summary.append({
            "code": lang,
            "name": meta["name"],
            "color": meta["color"],
            "percentage": pct
        })
        
    metrics = {
        "total_tokens": len(tokens),
        "total_spans": len(spans),
        "latency_ms": round(latency, 2),
        "languages": lang_summary,
        "stages": stages_count,
        "models": models_count
    }
    
    return jsonify({
        "spans": spans,
        "enriched_spans": enriched_spans,
        "tokens": tokens,
        "metrics": metrics
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "="*70)
    print(" POLYLID ACADEMIC WORKBENCH STARTED")
    print("="*70)
    print(f" Web application running at: http://localhost:{port}")
    print("="*70 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)


