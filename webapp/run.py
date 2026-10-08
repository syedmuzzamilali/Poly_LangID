import os
import sys

# Ensure webapp directory is on sys.path
webapp_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, webapp_dir)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "=" * 70)
    print(" POLYLID ACADEMIC WORKBENCH STARTED")
    print("=" * 70)
    print(f" Web application running at: http://localhost:{port}")
    print("=" * 70 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)
