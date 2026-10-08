import json, csv, os, glob

lang_map_char = {}  # will infer from indices

def convert_zh_en_csv(csv_path):
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row.get('original', '').strip()
            cs_indices_raw = row.get('indicesOfCS', '').strip().strip('[]')
            punct_raw = row.get('punctOriginal', '').strip().strip('[]')
            
            tokens = original.split()
            if not tokens:
                continue
            
            # Parse code-switched indices
            cs_idx = set()
            if cs_indices_raw:
                for idx in cs_indices_raw.split('_'):
                    try:
                        cs_idx.add(int(idx))
                    except ValueError:
                        pass
            
            punct_idx = set()
            if punct_raw:
                for idx in punct_raw.split('_'):
                    try:
                        punct_idx.add(int(idx))
                    except ValueError:
                        pass
            
            # Assign labels
            tagged_parts = []
            for i, tok in enumerate(tokens):
                if i in punct_idx:
                    lang = 'und'
                elif i in cs_idx:
                    lang = 'en'
                else:
                    lang = 'zh'
                tagged_parts.append(f'[{lang}] {tok}')
            
            raw_text = ' '.join(tokens)
            tagged_text = ' '.join(tagged_parts)
            rows.append({'raw_text': raw_text, 'tagged_text': tagged_text})
    return rows

# Collect all validation CSVs
all_rows = []
pattern = 'datasets/chinese_english_raw/data/validation/*.csv'
for csv_path in sorted(glob.glob(pattern)):
    if 'cs_index' not in csv_path:
        rows = convert_zh_en_csv(csv_path)
        all_rows.extend(rows)
        print(f'  {os.path.basename(csv_path)}: {len(rows)} sentences')

# Deduplicate by raw_text
seen = set()
unique = []
for r in all_rows:
    if r['raw_text'] not in seen:
        seen.add(r['raw_text'])
        unique.append(r)

with open('datasets/chinese_english.jsonl', 'w', encoding='utf-8') as f:
    for r in unique:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f'Total unique sentences: {len(unique)} -> datasets/chinese_english.jsonl')
