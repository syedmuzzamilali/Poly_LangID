import os
import sys
import time
import json
from flask import Flask, render_template, request, jsonify

# Add parent directory to sys.path to import polybeta module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import polybeta

app = Flask(__name__, template_folder="templates", static_folder="static")

# Global singleton detector
print("Initializing PolyBeta (LID V5 Standalone) Framework for Web Workbench...")
start_init = time.time()
detector = polybeta.get_detector()
init_time = (time.time() - start_init) * 1000
print(f"PolyBeta V5 Framework initialized successfully in {init_time:.2f} ms.")

@app.route("/")
def index():
    return render_template("index.html")

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
        return jsonify({"spans": [], "tokens": [], "latency_ms": 0.0, "metrics": {}})
        
    start_t = time.time()
    active_det = polybeta.get_detector()
    spans = active_det.detect_languages(text, allowed_langs=allowed)
    tokens = active_det.identify_to_dict(text, allowed_langs=allowed)
    latency = (time.time() - start_t) * 1000.0
    
    # Calculate metrics
    stages_count = {}
    models_count = {}
    for t in tokens:
        dec = str(t.get("decided_by", "Unknown"))
        reason = str(t.get("reason", ""))
        models_count[dec] = models_count.get(dec, 0) + 1
        if "LocalContext" in dec or "Local/Dissenting" in reason:
            stage = "Level 3 (Local Context Refinement)"
        elif "Consensus" in reason or "+" in dec or "Unanimous" in reason:
            stage = "Stage 1 (Consensus Building)"
        else:
            stage = "Stage 2 (Evidence Comparison)"
        stages_count[stage] = stages_count.get(stage, 0) + 1
        
    metrics = {
        "total_tokens": len(tokens),
        "total_spans": len(spans),
        "latency_ms": round(latency, 2),
        "stages": stages_count,
        "models": models_count
    }
    
    return jsonify({
        "spans": spans,
        "tokens": tokens,
        "metrics": metrics
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "="*70)
    print(" POLYLID ACADEMIC WORKBENCH STARTED SUCCESSFULLY (POLYBETA V5)")
    print("="*70)
    print(f" Open your web browser and navigate to: http://localhost:{port}")
    print("="*70 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)

