import os
import json
import re
from collections import Counter
import pandas as pd
from polylid import get_detector
from polylid_eval import tokenize, build_ordered_span_ranges, dominant_script_for_text, normalize_lang_tag
from evaluation.label_audit import DATASETS

def audit_arabic_script():
    config = DATASETS["arabic_english"]
    dataset = []
    with open(config["path"], "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            obj = json.loads(line)
            if "tagged_text" in obj:
                raw_text = obj.get("raw_text", "")
                spans = []
                matches = re.finditer(r"\[([a-zA-Z0-9]{2,5})\]\s*([^\[]+)", obj["tagged_text"])
                for match in matches:
                    text = match.group(2).strip()
                    lang = match.group(1).strip().lower()
                    if text:
                        spans.append({"text": text, "lang": lang})
                if spans:
                    dataset.append({"text": raw_text, "spans": spans, "id": len(dataset)})
                    
    detector = get_detector()
    allowed_langs = config["allowed_langs"]
    mapping = config["mapping"]
    
    arabizi_errors = []
    script_breakdown = {
        "ar_arabic": {"total": 0, "correct": 0},
        "ar_latin": {"total": 0, "correct": 0},
        "ar_mixed": {"total": 0, "correct": 0},
        "ar_other": {"total": 0, "correct": 0},
        "en_all": {"total": 0, "correct": 0}
    }
    
    print("Starting script breakdown for Arabic-English...")
    for item in dataset:
        sent = item["text"]
        pred_spans = detector.detect_languages(sent, allowed_langs=allowed_langs)
        gold_spans = item["spans"]
        
        tokens = tokenize(sent)
        token_ranges = []
        cursor = 0
        for t in tokens:
            s = sent.find(t, cursor)
            if s == -1: s = sent.find(t)
            if s == -1: continue
            e = s + len(t)
            token_ranges.append((s, e))
            cursor = e
            
        gold_ranges = build_ordered_span_ranges(sent, gold_spans, tuple_mode=False)
        pred_ranges = build_ordered_span_ranges(sent, pred_spans, tuple_mode=True)
        
        def tag_for(start, end, ranges):
            best_lang = "und"
            best_ov = 0
            for st, en, lang in ranges:
                ov = max(0, min(end, en) - max(start, st))
                if ov > best_ov:
                    best_ov = ov
                    best_lang = lang
            return best_lang
            
        gold_tags_raw = [tag_for(s, e, gold_ranges) for s, e in token_ranges]
        pred_tags_raw = [tag_for(s, e, pred_ranges) for s, e in token_ranges]
        
        gold_tags_mapped = [mapping.get(gt, "und") for gt in gold_tags_raw]
        pred_tags_mapped = [normalize_lang_tag(pt) for pt in pred_tags_raw]
        
        for idx in range(len(gold_tags_mapped)):
            g_mapped = gold_tags_mapped[idx]
            p_mapped = pred_tags_mapped[idx]
            if g_mapped in ("un", "und"):
                continue
                
            token_str = sent[token_ranges[idx][0]:token_ranges[idx][1]]
            script = dominant_script_for_text(token_str)
            
            is_correct = (g_mapped == p_mapped)
            
            if g_mapped == "ar":
                if script.lower() == "arabic":
                    bucket = "ar_arabic"
                elif script.lower() == "latin":
                    bucket = "ar_latin"
                elif script.lower() == "mixed":
                    bucket = "ar_mixed"
                else:
                    bucket = "ar_other"
            else:
                bucket = "en_all"
                
            script_breakdown[bucket]["total"] += 1
            if is_correct:
                script_breakdown[bucket]["correct"] += 1
            elif bucket == "ar_latin":
                arabizi_errors.append({
                    "sentence_id": item["id"],
                    "token_id": idx,
                    "token": token_str,
                    "script": script,
                    "gold": g_mapped,
                    "pred": p_mapped
                })
                
    results = []
    for bucket, stats in script_breakdown.items():
        total = stats["total"]
        acc = stats["correct"] / total if total > 0 else 0
        results.append({"Category": bucket, "Total Tokens": total, "Correct": stats["correct"], "Accuracy": acc})
        print(f"{bucket}: {stats['correct']}/{total} ({acc*100:.2f}%)")
        
    ar_total = script_breakdown["ar_arabic"]["total"] + script_breakdown["ar_latin"]["total"] + script_breakdown["ar_mixed"]["total"] + script_breakdown["ar_other"]["total"]
    if ar_total > 0:
        arabizi_pct = script_breakdown["ar_latin"]["total"] / ar_total
        print(f"Arabizi percentage among Arabic-labelled tokens: {arabizi_pct*100:.2f}%")
        
    df = pd.DataFrame(results)
    df.to_csv("results/audits/arabic_english_script_breakdown.csv", index=False)
    
    err_df = pd.DataFrame(arabizi_errors)
    err_df.to_csv("results/audits/arabic_english_arabizi_errors.csv", index=False)

if __name__ == "__main__":
    audit_arabic_script()
