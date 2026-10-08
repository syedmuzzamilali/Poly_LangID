import subprocess, os, re, json

datasets = [
    ('Indonesian-English', 'datasets/indonesian_english.jsonl', 'Indonesian + English', 'Latin'),
    ('Spanish-English (LinCE)', 'datasets/lince_spaeng.json', 'Spanish + English', 'Latin'),
    ('Turkish-English (LinCE)', 'datasets/lince_turen.json', 'Turkish + English', 'Latin'),
    ('German-English (Denglisch)', 'datasets/german_english.jsonl', 'German + English', 'Latin'),
    ('Sinhala-English', 'datasets/sinhala_english.jsonl', 'Sinhala + English', 'Sinhala script'),
    ('Turkish-German', 'datasets/turkish_german.jsonl', 'Turkish + German', 'Latin'),
    ('German-English (TongueSwitcher)', 'datasets/tongueswitcher_de_en.jsonl', 'German + English', 'Latin'),
    ('Chinese-English', 'datasets/chinese_english.jsonl', 'Chinese + English', 'Chinese characters'),
]

results = []
for name, ds, langs, script in datasets:
    if not os.path.exists(ds):
        print(f'SKIPPED {name}: file not found')
        continue
    print(f'Evaluating {name}...')
    subprocess.run([r'.\\.venv\\Scripts\\python.exe', 'polylid_eval.py', '--dataset', ds, '--limit', '1000'])
    if os.path.exists('PolyBench_Report.md'):
        with open('PolyBench_Report.md', 'r', encoding='utf-8') as f:
            md = f.read()
        # Extract metrics
        m = re.search(r'polylid\s+macro_f1=\s*([\d.]+)\s+token_acc=\s*([\d.]+)\s+boundary_f1=\s*([\d.]+)\s+EM=\s*([\d.]+)\s+PM=\s*([\d.]+)', md)
        if not m:
            # try from log output format
            m2 = re.search(r'polylid macro_f1=\s*([\d.]+)\s+token_acc=\s*([\d.]+)\s+boundary_f1=\s*([\d.]+)\s+EM=\s*([\d.]+)\s+PM=\s*([\d.]+)', md)
            if m2: m = m2
        if m:
            mf1, tacc, bf1, em, pm = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            results.append({'name': name, 'langs': langs, 'script': script,
                           'tacc': float(tacc), 'mf1': float(mf1), 'bf1': float(bf1),
                           'em': float(em), 'pm': float(pm), 'detail_md': md})
            print(f'  -> tacc={tacc}, mf1={mf1}, em={em}, pm={pm}')

# Write clean results to JSON for report generation
with open('final_results.json', 'w', encoding='utf-8') as f:
    json.dump([{k:v for k,v in r.items() if k!='detail_md'} for r in results], f, indent=2)
print(f'\nCompleted {len(results)}/{len(datasets)} evaluations')
