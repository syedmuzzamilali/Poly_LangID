import json
import os
import re
from collections import Counter
import ast
import pandas as pd

DATASETS = {
    "chinese_english": {
        "path": "datasets/chinese_english.jsonl",
        "type": "jsonl_tagged",
        "allowed_langs": ["zh", "en"],
        "mapping": {
            "zh": "zh", "en": "en", 
            "un": "un", "und": "und", "mixed": "und"
        },
        "ignored_reasons": {
            "un": "Punctuation/Unknown",
            "und": "Undefined/Ambiguous",
            "mixed": "Mixed language within token"
        }
    },
    "arabic_english": {
        "path": "datasets/arabic_english.jsonl",
        "type": "jsonl_tagged",
        "allowed_langs": ["ar", "en"],
        "mapping": {
            "ar": "ar", "en": "en", 
            "un": "un", "und": "und",
            "ambiguous": "und", "ne": "und"
        },
        "ignored_reasons": {
            "un": "Punctuation",
            "und": "Undefined",
            "ambiguous": "Ambiguous token",
            "ne": "Named entity (can be lang neutral)"
        }
    },
    "indonesian_english": {
        "path": "datasets/indonesian_english.jsonl",
        "type": "jsonl_tagged",
        "allowed_langs": ["id", "en"],
        "mapping": {
            "id": "id", "en": "en", "in": "id", "eng": "en", "ind": "id",
            "un": "un", "und": "und", "mixed": "und"
        },
        "ignored_reasons": {
            "un": "Punctuation",
            "und": "Undefined",
            "mixed": "Mixed"
        }
    },
    "tongueswitcher_de_en": {
        "path": "datasets/tongueswitcher_de_en.jsonl",
        "type": "jsonl_tagged",
        "allowed_langs": ["de", "en"],
        "mapping": {
            "de": "de", "en": "en", "ger": "de",
            "un": "un", "und": "de", "other": "und", "mix": "und", "ost": "und",
            "117": "un", "120": "un", "121": "un", "31": "un", "32": "un",
            "63": "un", "172": "un", "173": "un", "174": "un",
            "12": "un", "14": "un", "15": "un"
        },
        "ignored_reasons": {
            "un": "Punctuation", "und": "Undefined", "other": "Other", "mix": "Mixed", "ost": "Other"
        }
    },
    "turkish_german": {
        "path": "datasets/turkish_german.jsonl",
        "type": "jsonl_tagged",
        "allowed_langs": ["tr", "de"],
        "mapping": {
            "tr": "tr", "de": "de", "ger": "de", "tur": "tr",
            "un": "un", "und": "und", "other": "und", "lang3": "und"
        },
        "ignored_reasons": {
            "un": "Punctuation", "und": "Undefined", "other": "Other", "lang3": "Third language"
        }
    },
    "lince_spaeng": {
        "path": "datasets/lince_spaeng.json",
        "type": "lince_json",
        "allowed_langs": ["es", "en"],
        "mapping": {
            "es": "es", "en": "en", "spa": "es", "eng": "en",
            "unk": "und", "mixed": "und", "other": "und", "ambiguous": "und", "ne": "und", "und": "und", "lang1": "es", "lang2": "en"
        },
        "ignored_reasons": {
            "unk": "Unknown", "mixed": "Mixed", "other": "Other", "ambiguous": "Ambiguous", "ne": "Named Entity", "und": "Undefined"
        }
    },
    "lince_turen": {
        "path": "datasets/lince_turen.json",
        "type": "lince_json",
        "allowed_langs": ["tr", "en"],
        "mapping": {
            "tr": "tr", "en": "en", "tur": "tr", "eng": "en",
            "unk": "und", "mixed": "und", "other": "und", "ambiguous": "und", "ne": "und", "und": "und", "lang1": "tr", "lang2": "en"
        },
        "ignored_reasons": {
            "unk": "Unknown", "mixed": "Mixed", "other": "Other", "ambiguous": "Ambiguous", "ne": "Named Entity", "und": "Undefined"
        }
    }
}

def load_dataset_raw_labels(config):
    path = config["path"]
    dtype = config["type"]
    labels = []
    
    if dtype == "jsonl_tagged":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                obj = json.loads(line)
                if "tagged_text" in obj:
                    matches = re.finditer(r"\[([a-zA-Z0-9]{2,5})\]\s*([^\[]+)", obj["tagged_text"])
                    for match in matches:
                        if match.group(2).strip():
                            labels.append(match.group(1).strip().lower())
    elif dtype == "lince_json":
        with open(path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
            # wait, how are spans loaded in polylid_eval.py?
            # It seems they use 'datasets/lince_spaeng.json' which might be list of dicts or {"data": ...}
            # Or wait, lince json might not even have spans directly like that, let me verify how polylid_eval.py loaded it.
            # In polylid_eval.py, if it's not .csv or .jsonl, it expects {"data": [{"native sentence": "", "language": ""}]} or it just loads it as list of {"text": "...", "spans": [{"text": "...", "lang": "..."}]}
            if isinstance(raw_json, dict) and "data" in raw_json:
                for item in raw_json["data"]:
                    lang = item.get("language", "").lower()
                    labels.append(lang)
            elif isinstance(raw_json, list):
                for item in raw_json:
                    for span in item.get("spans", []):
                        labels.append(str(span.get("lang", "")).lower())
    return labels

def audit_dataset(name, config):
    print(f"Auditing {name}...")
    try:
        raw_labels = load_dataset_raw_labels(config)
    except Exception as e:
        print(f"Error loading {name}: {e}")
        return
        
    raw_freq = Counter(raw_labels)
    print("Raw label frequencies:", raw_freq)
    
    mapping = config["mapping"]
    mapped_freq = Counter()
    ignored_freq = Counter()
    
    for raw in raw_labels:
        if raw not in mapping:
            # Need to discover what unknown labels exist to fail gracefully
            raise ValueError(f"Unknown label encountered in {name}: '{raw}'")
        mapped = mapping[raw]
        mapped_freq[mapped] += 1
        
        if mapped == "un" or mapped == "und":
            ignored_freq[raw] += 1
            
    print("Mapped label frequencies:", mapped_freq)
    print("Ignored labels:", ignored_freq)
    
    # 6. Confirm allowed_langs contains intended language pair
    for lang in config["allowed_langs"]:
        if lang not in mapped_freq and lang not in raw_freq:
            print(f"WARNING: Intended language {lang} not found in {name}!")
            
    # 7. Verify gold labels are not accidentally reversed
    # E.g., if one language has extremely low count compared to the other when they should be somewhat balanced
    
    # Save to json
    audit_data = {
        "dataset": name,
        "raw_label_frequency": dict(raw_freq),
        "mapped_label_frequency": dict(mapped_freq),
        "ignored_label_frequency": dict(ignored_freq),
        "ignored_reasons": config["ignored_reasons"],
        "allowed_languages": config["allowed_langs"],
        "mapping": mapping
    }
    
    os.makedirs("results/benchmarks", exist_ok=True)
    out_path = f"results/benchmarks/{name}_label_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Saved audit to {out_path}\n")

if __name__ == "__main__":
    for name, config in DATASETS.items():
        audit_dataset(name, config)
