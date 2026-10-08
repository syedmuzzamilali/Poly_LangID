import json
import csv

def process_conll_format(in_path, out_path, lang_map):
    dataset = []
    with open(in_path, 'r', encoding='utf-8') as f:
        spans = []
        raw_text = []
        for line in f:
            line = line.strip()
            if not line:
                if spans:
                    dataset.append({
                        "raw_text": " ".join(raw_text),
                        "tagged_text": " ".join(f"[{s['lang']}] {s['text']}" for s in spans)
                    })
                    spans = []
                    raw_text = []
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0].strip()
                tag = parts[1].strip()
                lang = lang_map.get(tag.lower(), "und")
                spans.append({"text": word, "lang": lang})
                raw_text.append(word)
        if spans:
            dataset.append({
                "raw_text": " ".join(raw_text),
                "tagged_text": " ".join(f"[{s['lang']}] {s['text']}" for s in spans)
            })
    with open(out_path, 'w', encoding='utf-8') as f:
        for d in dataset:
            f.write(json.dumps(d) + '\n')
    print(f"Processed {in_path} -> {out_path} ({len(dataset)} samples)")

# Telugu
process_conll_format(
    'datasets/telugu_english_raw/Data/Codemixed.txt',
    'datasets/telugu_english.jsonl',
    {'te': 'te', 'en': 'en', 'univ': 'und', 'ne': 'und'}
)

# Hindi
process_conll_format(
    'datasets/hindi_english_raw/L3Cube-HingLID/all.txt',
    'datasets/hindi_english.jsonl',
    {'hi': 'hi', 'en': 'en', 'univ': 'und', 'ne': 'und', 'other': 'und'}
)

# Sinhala
def process_sinhala(in_path, out_path):
    dataset = []
    current_sen = None
    spans = []
    raw_text = []
    
    with open(in_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sen_id = row['SenId']
            word = row['Words']
            tag = row['LID']
            
            if current_sen is not None and sen_id != current_sen:
                if spans:
                    dataset.append({
                        "raw_text": " ".join(raw_text),
                        "tagged_text": " ".join(f"[{s['lang']}] {s['text']}" for s in spans)
                    })
                spans = []
                raw_text = []
            
            current_sen = sen_id
            
            lang = "und"
            if tag == "Sin-Eng":
                lang = "si"
            elif tag == "English":
                lang = "en"
                
            spans.append({"text": word, "lang": lang})
            raw_text.append(word)
            
        if spans:
            dataset.append({
                "raw_text": " ".join(raw_text),
                "tagged_text": " ".join(f"[{s['lang']}] {s['text']}" for s in spans)
            })
            
    with open(out_path, 'w', encoding='utf-8') as f:
        for d in dataset:
            f.write(json.dumps(d) + '\n')
    print(f"Processed {in_path} -> {out_path} ({len(dataset)} samples)")

process_sinhala('datasets/sinhala_english_raw/word-level-annotation.csv', 'datasets/sinhala_english.jsonl')

