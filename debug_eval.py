import json
from polylid_eval import evaluate_one

with open('datasets/indonesian_english.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

dataset = []
for line in lines[:5]:
    obj = json.loads(line)
    if 'tagged_text' in obj:
        import re
        raw_text = obj.get('raw_text', '')
        spans = []
        for match in re.finditer(r"\[([a-z]{2,3})\]\s*([^\[]+)", obj['tagged_text']):
            spans.append({'text': match.group(2).strip(), 'lang': match.group(1).strip()})
        dataset.append({'text': raw_text, 'spans': spans})

print("First dataset element:", dataset[0])

try:
    evaluate_one('polylid', dataset)
except Exception as e:
    import traceback
    traceback.print_exc()
