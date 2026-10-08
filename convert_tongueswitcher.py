import json, csv

lang_map = {
    'E': 'en', 'G': 'de', 'O': 'und', 'SO': 'und',
    'NE': 'und', 'C': 'und', 'M': 'und'
}

sentences = {}
with open('datasets/tongueswitcher_raw/data/denglisch/Manu_corpus_collapsed.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['user_name'], row['sen_id'])
        if key not in sentences:
            sentences[key] = []
        lang = lang_map.get(row['categ'], 'und')
        sentences[key].append({'word': row['token'], 'lang': lang})

dataset = []
for key, tokens in sentences.items():
    raw = ' '.join(t['word'] for t in tokens)
    tagged = ' '.join(f"[{t['lang']}] {t['word']}" for t in tokens)
    dataset.append({'raw_text': raw, 'tagged_text': tagged})

with open('datasets/tongueswitcher_de_en.jsonl', 'w', encoding='utf-8') as f:
    for d in dataset:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')
        
print(f'Converted {len(dataset)} sentences -> datasets/tongueswitcher_de_en.jsonl')
