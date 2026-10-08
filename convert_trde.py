import json

def convert_trde(in_path, out_path):
    lang_map = {
        'TR': 'tr', 'DE': 'de', 'EN': 'en', 'MIX': 'und',
        'OTHER': 'und', 'AMB': 'und', 'NE': 'und', 'UNIV': 'und'
    }
    dataset = []
    current_sid = None
    tokens = []
    
    with open(in_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            sid, orig, norm, tag = parts[0], parts[1], parts[2], parts[3]
            if current_sid is not None and sid != current_sid:
                if tokens:
                    tagged = ' '.join(f"[{t['lang']}] {t['word']}" for t in tokens)
                    raw = ' '.join(t['word'] for t in tokens)
                    dataset.append({'raw_text': raw, 'tagged_text': tagged})
                tokens = []
            current_sid = sid
            lang = lang_map.get(tag.upper(), 'und')
            tokens.append({'word': orig, 'lang': lang})
    
    if tokens:
        tagged = ' '.join(f"[{t['lang']}] {t['word']}" for t in tokens)
        raw = ' '.join(t['word'] for t in tokens)
        dataset.append({'raw_text': raw, 'tagged_text': tagged})
    
    with open(out_path, 'w', encoding='utf-8') as f:
        for d in dataset:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print(f"Converted {len(dataset)} sentences -> {out_path}")

convert_trde(
    'datasets/turkish_german_raw/train/trde_twitter.train.simp_orig_norm.giza_man.algn.lid',
    'datasets/turkish_german.jsonl'
)
