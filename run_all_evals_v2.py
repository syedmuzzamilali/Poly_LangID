import subprocess
import os

datasets = [
    ("Indonesian-English", "datasets/indonesian_english.jsonl"),
    ("Spanish-English (LinCE)", "datasets/lince_spaeng.json"),
    ("Turkish-English (LinCE)", "datasets/lince_turen.json"),
    ("German-English (Denglisch)", "datasets/german_english.jsonl"),
    ("Arabic-English", "datasets/arabic_english.jsonl"),
    ("Telugu-English", "datasets/telugu_english.jsonl"),
    ("Hindi-English", "datasets/hindi_english.jsonl"),
    ("Sinhala-English", "datasets/sinhala_english.jsonl"),
    ("Turkish-German", "datasets/turkish_german.jsonl"),
    ("German-English (TongueSwitcher)", "datasets/tongueswitcher_de_en.jsonl"),
]

results = []
for name, ds in datasets:
    print(f"Evaluating {name}...")
    subprocess.run([".\\.venv\\Scripts\\python.exe", "polylid_eval.py", "--dataset", ds, "--limit", "1000"])
    if os.path.exists("PolyBench_Report.md"):
        with open("PolyBench_Report.md", "r", encoding="utf-8") as f:
            md = f.read()
        results.append((name, md))
    else:
        print(f"Warning: No report for {name}")

# Build combined report
header = """# PolyLID Comprehensive Cross-Dataset Evaluation Report

**Date**: September 2026  
**Metrics**: Token Accuracy, Macro F1, Boundary F1, Exact Match (EM), Partial Match (PM)  
**Note**: Each dataset capped at 1,000 sentences for consistent comparison. EM/PM calculated after filtering [un] tags.

## Quick Reference Table

| Dataset | Languages | Token Acc | Macro F1 | EM | PM |
|:--------|:----------|----------:|---------:|---:|---:|
"""

rows = []
for name, md in results:
    import re
    m = re.search(r'polylid\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|.*?\|\s+([\d.]+)\s+\|\s+([\d.]+)', md)
    if m:
        tacc, mf1, em, pm = m.group(1), m.group(2), m.group(3), m.group(4)
        rows.append(f"| {name} | - | {float(tacc):.1%} | {float(mf1):.4f} | {float(em):.1%} | {float(pm):.1%} |")

content = header + "\n".join(rows) + "\n\n---\n\n"
for name, md in results:
    content += f"\n\n# Dataset: {name}\n\n" + md

output_path = "C:/Users/takweer/.gemini/antigravity-ide/brain/40b56767-284a-42f9-9c5f-b23627352fe5/evaluation_report.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"All {len(results)} evaluations complete. Report written.")
