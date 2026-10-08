import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("results/environment.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def command_output(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"Unavailable: {exc}"

snapshot = {
    "execution_time_utc": datetime.now(timezone.utc).isoformat(),
    "python_version": sys.version,
    "python_executable": sys.executable,
    "operating_system": platform.platform(),
    "processor": platform.processor(),
    "machine": platform.machine(),
    "cpu_count": os.cpu_count(),
    "git_revision": command_output(
        ["git", "rev-parse", "HEAD"]
    ),
    "git_status": command_output(
        ["git", "status", "--short"]
    ),
    "pip_freeze": command_output(
        [sys.executable, "-m", "pip", "freeze"]
    ),
}

OUTPUT.write_text(
    json.dumps(snapshot, indent=2),
    encoding="utf-8",
)
print(f"Saved environment information to {OUTPUT}")
