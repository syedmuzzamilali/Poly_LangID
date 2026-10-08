import subprocess
import sys

datasets = [
    ("datasets/lince_spaeng.json", "eval_spa_eng.md", None),
    ("datasets/lince_turen.json", "eval_tur_eng.md", None),
    ("datasets/arabic_english.jsonl", "eval_ara_eng.md", None),
    ("datasets/german_english.jsonl", "eval_deu_eng.md", 3000)
]

for ds, report, limit in datasets:
    cmd = [r".\.venv\Scripts\python.exe", "polylid_eval.py", "--dataset", ds, "--report", report]
    if limit:
        cmd.extend(["--limit", str(limit)])
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error evaluating {ds}: {e}")
print("All evaluations finished!")
