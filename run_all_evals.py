import subprocess
import os

datasets = [
    "datasets/indonesian_english.jsonl",
    "datasets/lince_spaeng.json",
    "datasets/lince_turen.json",
    "datasets/german_english.jsonl",
    "datasets/arabic_english.jsonl",
    "datasets/telugu_english.jsonl",
    "datasets/hindi_english.jsonl",
    "datasets/sinhala_english.jsonl"
]

all_md_content = "# Comprehensive PolyLID Evaluation Report (EM/PM)\n\n"
all_md_content += "Note: Datasets were limited to a maximum of 2,500 sentences each to complete evaluation within a reasonable timeframe.\n\n"

for ds in datasets:
    print(f"Evaluating {ds}...")
    subprocess.run([".\\.venv\\Scripts\\python.exe", "polylid_eval.py", "--dataset", ds, "--limit", "2500"])
    
    if os.path.exists("PolyBench_Report.md"):
        with open("PolyBench_Report.md", "r", encoding="utf-8") as f:
            md = f.read()
        
        all_md_content += f"\n\n# Dataset: {os.path.basename(ds)}\n\n"
        all_md_content += md
    else:
        print(f"Warning: PolyBench_Report.md not found for {ds}")

with open("C:/Users/takweer/.gemini/antigravity-ide/brain/40b56767-284a-42f9-9c5f-b23627352fe5/evaluation_report.md", "w", encoding="utf-8") as f:
    f.write(all_md_content)
    
print("All evaluations complete. evaluation_report.md updated.")
