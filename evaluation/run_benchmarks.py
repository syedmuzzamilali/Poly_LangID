import os
import json
import csv
import pandas as pd
from polylid import get_detector
from evaluation.label_audit import load_dataset_raw_labels, DATASETS
from evaluation.metrics import (
    token_accuracy,
    strict_exact_match,
    sentence_partial_match,
    boundary_metrics,
    per_language_metrics
)
from polylid_eval import tokenize, build_ordered_span_ranges, normalize_lang_tag

def run_benchmarks():
    print("Starting full benchmark rerun...")
    detector = get_detector()
    
    results = []
    os.makedirs("results/benchmarks", exist_ok=True)
    
    for name, config in DATASETS.items():
        print(f"Evaluating {name}...")
        
        path = config["path"]
        dataset = []
        # Load data
        if config["type"] == "jsonl_tagged":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    obj = json.loads(line)
                    if "tagged_text" in obj:
                        import re
                        raw_text = obj.get("raw_text", "")
                        spans = []
                        matches = re.finditer(r"\[([a-zA-Z0-9]{2,5})\]\s*([^\[]+)", obj["tagged_text"])
                        for match in matches:
                            text = match.group(2).strip()
                            lang = match.group(1).strip().lower()
                            if text:
                                spans.append({"text": text, "lang": lang})
                        if spans:
                            dataset.append({"text": raw_text, "spans": spans})
        elif config["type"] == "lince_json":
            with open(path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
                if isinstance(raw_json, list):
                    for item in raw_json:
                        raw_text = item.get("text", "")
                        spans = item.get("spans", [])
                        if raw_text and spans:
                            dataset.append({"text": raw_text, "spans": spans})
                            
        if not dataset:
            print(f"Warning: {name} dataset is empty or failed to load properly.")
            continue
        import random
        random.seed(42)
        if len(dataset) > 1000:
            dataset = random.sample(dataset, 1000)
            
        allowed_langs = config["allowed_langs"]
        mapping = config["mapping"]
        
        texts = [x["text"] for x in dataset]
        predictions = [detector.detect_languages(t, allowed_langs=allowed_langs) for t in texts]
        
        Y_TRUE = []
        Y_PRED = []
        gold_seqs = []
        pred_seqs = []
        
        for sent, gold_spans, pred_spans in zip(texts, [x["spans"] for x in dataset], predictions):
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
            
            # Map gold tags using the dataset-specific audit mapping
            gold_tags_mapped = [mapping.get(gt, "und") for gt in gold_tags_raw]
            # Normalizing pred tags, but they should already be standard ISO codes
            pred_tags_mapped = [normalize_lang_tag(pt) for pt in pred_tags_raw]
            
            valid_indices = [idx for idx, g in enumerate(gold_tags_mapped) if g not in ("un", "und")]
            
            gold_tags_filtered = [gold_tags_mapped[idx] for idx in valid_indices]
            pred_tags_filtered = [pred_tags_mapped[idx] for idx in valid_indices]
            
            if not gold_tags_filtered:
                continue
                
            gold_seqs.append(gold_tags_filtered)
            pred_seqs.append(pred_tags_filtered)
            
            for idx in valid_indices:
                Y_TRUE.append(gold_tags_mapped[idx])
                Y_PRED.append(pred_tags_mapped[idx])
                
        # Metrics Calculation
        tok_acc = token_accuracy(Y_TRUE, Y_PRED) if Y_TRUE else 0.0
        em = strict_exact_match(gold_seqs, pred_seqs) if gold_seqs else 0.0
        pm = sentence_partial_match(gold_seqs, pred_seqs) if gold_seqs else 0.0
        bm = boundary_metrics(gold_seqs, pred_seqs, ignored_labels={"un", "und"})
        per_lang = per_language_metrics(Y_TRUE, Y_PRED) if Y_TRUE else {}
        
        # We need macro/weighted F1 overall for the valid tokens
        macro_f1 = per_lang.get("macro_f1", 0.0)
        weighted_f1 = per_lang.get("weighted_f1", 0.0)
        
        results.append({
            "dataset": name,
            "sentences": len(gold_seqs),
            "tokens": len(Y_TRUE),
            "token_accuracy": tok_acc,
            "exact_match": em,
            "partial_match": pm,
            "boundary_f1": bm["boundary_f1"],
            "boundary_precision": bm["boundary_precision"],
            "boundary_recall": bm["boundary_recall"],
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1
        })
        
        print(f"  Token Acc: {tok_acc:.4f} | EM: {em:.4f} | PM: {pm:.4f} | Boundary F1: {bm['boundary_f1']:.4f}")
        
    df = pd.DataFrame(results)
    df.to_csv("results/benchmarks/benchmark_results.csv", index=False)
    print("\nBenchmark results saved to results/benchmarks/benchmark_results.csv")
    
if __name__ == "__main__":
    run_benchmarks()
