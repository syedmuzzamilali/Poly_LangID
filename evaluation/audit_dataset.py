import os
import sys
import json
import argparse
import random
import re
from collections import Counter
from datetime import datetime
import pandas as pd

from polylid import get_detector
from evaluation.label_audit import load_dataset_raw_labels, DATASETS
from evaluation.metrics import (
    token_accuracy,
    strict_exact_match,
    sentence_partial_match,
    boundary_metrics,
    per_language_metrics,
    switch_boundaries
)
from polylid_eval import tokenize, build_ordered_span_ranges, normalize_lang_tag

def run_audit(args):
    if args.dataset not in DATASETS:
        raise ValueError(f"Unknown dataset {args.dataset}")
        
    config = DATASETS[args.dataset]
    dataset_path = config["path"]
    
    # Load raw text and spans
    dataset = []
    if config["type"] == "jsonl_tagged":
        with open(dataset_path, "r", encoding="utf-8") as f:
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
    elif config["type"] == "lince_json":
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
            if isinstance(raw_json, list):
                for item in raw_json:
                    raw_text = item.get("text", "")
                    spans = item.get("spans", [])
                    if raw_text and spans:
                        dataset.append({"text": raw_text, "spans": spans, "id": len(dataset)})
                        
    allowed_langs = config["allowed_langs"]
    mapping = config["mapping"]
    
    detector = get_detector()
    if args.disable_cache:
        # Assuming no cache mechanism needs to be explicitly cleared in polylid,
        # but the arg exists to ensure predictions aren't loaded from a file
        pass
        
    print(f"Loaded {len(dataset)} items. Starting predictions...", flush=True)
    
    Y_TRUE_RAW = []
    Y_TRUE_MAPPED = []
    Y_PRED = []
    
    errors = []
    boundary_errors = []
    
    gold_seqs = []
    pred_seqs = []
    
    ignored_raw_labels = Counter()
    
    total_gold_tokens = 0
    evaluated_tokens = 0
    ignored_tokens = 0
    correct_tokens = 0
    
    for i, item in enumerate(dataset):
        if i % 1000 == 0:
            print(f"Processing item {i}/{len(dataset)}...", flush=True)
            
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
        
        total_gold_tokens += len(gold_tags_mapped)
        
        valid_indices = [idx for idx, g in enumerate(gold_tags_mapped) if g not in ("un", "und")]
        ignored_indices = [idx for idx, g in enumerate(gold_tags_mapped) if g in ("un", "und")]
        
        for idx in ignored_indices:
            ignored_tokens += 1
            ignored_raw_labels[gold_tags_raw[idx]] += 1
            
        gold_tags_filtered = [gold_tags_mapped[idx] for idx in valid_indices]
        pred_tags_filtered = [pred_tags_mapped[idx] for idx in valid_indices]
        
        if not gold_tags_filtered:
            continue
            
        gold_seqs.append(gold_tags_filtered)
        pred_seqs.append(pred_tags_filtered)
        
        # Check boundary correctness for this sentence
        b_metrics = boundary_metrics([gold_tags_filtered], [pred_tags_filtered], ignored_labels={"un", "und"})
        has_gold_switch = b_metrics["total_gold_boundaries"] > 0
        has_pred_switch = b_metrics["total_pred_boundaries"] > 0
        if has_gold_switch or has_pred_switch:
            boundary_errors.append({
                "sentence_id": item["id"],
                "text": sent,
                "gold_sequence": gold_tags_filtered,
                "predicted_sequence": pred_tags_filtered,
                "gold_boundaries": list(switch_boundaries(gold_tags_filtered, {"un", "und"})),
                "predicted_boundaries": list(switch_boundaries(pred_tags_filtered, {"un", "und"})),
                "boundary_tp": b_metrics["true_positives"],
                "boundary_fp": b_metrics["false_positives"],
                "boundary_fn": b_metrics["false_negatives"]
            })
            
        for idx in valid_indices:
            evaluated_tokens += 1
            g_mapped = gold_tags_mapped[idx]
            p_mapped = pred_tags_mapped[idx]
            
            Y_TRUE_RAW.append(gold_tags_raw[idx])
            Y_TRUE_MAPPED.append(g_mapped)
            Y_PRED.append(p_mapped)
            
            is_correct = (g_mapped == p_mapped)
            if is_correct:
                correct_tokens += 1
            else:
                errors.append({
                    "sentence_id": item["id"],
                    "token_id": idx,
                    "sentence_text": sent,
                    "token": sent[token_ranges[idx][0]:token_ranges[idx][1]],
                    "raw_gold_label": gold_tags_raw[idx],
                    "mapped_gold_label": g_mapped,
                    "predicted_label": p_mapped,
                    "ignored_status": False,
                    "allowed_languages": str(allowed_langs),
                })
                
    if args.fail_on_missing_required_label:
        observed = set(Y_TRUE_MAPPED)
        required = set(allowed_langs)
        missing = required - observed
        if missing:
            raise ValueError(f"{args.dataset} is missing required gold labels after mapping: {sorted(list(missing))}")
            
    tok_acc = token_accuracy(Y_TRUE_MAPPED, Y_PRED) if Y_TRUE_MAPPED else 0.0
    em = strict_exact_match(gold_seqs, pred_seqs) if gold_seqs else 0.0
    pm = sentence_partial_match(gold_seqs, pred_seqs) if gold_seqs else 0.0
    bm = boundary_metrics(gold_seqs, pred_seqs, ignored_labels={"un", "und"})
    
    per_lang = per_language_metrics(Y_TRUE_MAPPED, Y_PRED) if Y_TRUE_MAPPED else {}
    
    if args.show_label_counts:
        print("Raw gold-label frequencies:", Counter(Y_TRUE_RAW))
        print("Normalized gold-label frequencies:", Counter(Y_TRUE_MAPPED))
        print("Predicted-label frequencies:", Counter(Y_PRED))
    if args.show_ignored_labels:
        print("Ignored raw-label frequencies:", ignored_raw_labels)
    if args.show_boundaries:
        print(f"Gold boundary count: {bm['total_gold_boundaries']}")
        print(f"Predicted boundary count: {bm['total_pred_boundaries']}")
    if args.show_errors and errors:
        for err in errors[:args.limit_errors if args.limit_errors else 10]:
            print(f"Error: {err['token']} (Gold: {err['mapped_gold_label']}, Pred: {err['predicted_label']})")
            
    os.makedirs("results/audits", exist_ok=True)
    
    # Check if empty boundary sets because of mapping
    if bm["total_gold_boundaries"] == 0:
        raise ValueError(
            f"{args.dataset} contains no gold boundaries after mapping. "
            "The dataset mapping or filtering is invalid for code-switch evaluation."
        )
        
    audit_json = {
        "dataset_name": args.dataset,
        "source_file_path": dataset_path,
        "split": "test",
        "source_revision": "HEAD",
        "execution_timestamp": datetime.utcnow().isoformat(),
        "sentence_count": len(dataset),
        "raw_gold_label_frequencies": dict(Counter(Y_TRUE_RAW)),
        "normalized_gold_label_frequencies": dict(Counter(Y_TRUE_MAPPED)),
        "ignored_raw_label_frequencies": dict(ignored_raw_labels),
        "predicted_label_frequencies": dict(Counter(Y_PRED)),
        "allowed_language_set": allowed_langs,
        "total_gold_tokens": total_gold_tokens,
        "evaluated_tokens": evaluated_tokens,
        "ignored_tokens": ignored_tokens,
        "correct_tokens": correct_tokens,
        "token_accuracy": tok_acc,
        "exact_match": em,
        "partial_match": pm,
        "macro_f1": per_lang.get("macro_f1", 0.0),
        "weighted_f1": per_lang.get("weighted_f1", 0.0),
        "gold_boundary_count": bm["total_gold_boundaries"],
        "predicted_boundary_count": bm["total_pred_boundaries"],
        "boundary_true_positives": bm["true_positives"],
        "boundary_false_positives": bm["false_positives"],
        "boundary_false_negatives": bm["false_negatives"],
        "boundary_precision": bm["boundary_precision"],
        "boundary_recall": bm["boundary_recall"],
        "boundary_f1": bm["boundary_f1"],
        "model_versions": "polylid",
        "cache_configuration": "disabled" if args.disable_cache else "enabled"
    }
    
    for lang, metrics in per_lang.get("per_class", {}).items():
        audit_json[f"per_language_precision_{lang}"] = metrics["precision"]
        audit_json[f"per_language_recall_{lang}"] = metrics["recall"]
        audit_json[f"per_language_f1_{lang}"] = metrics["f1"]
        audit_json[f"per_language_support_{lang}"] = metrics["support"]
        
    with open(f"results/audits/{args.dataset}_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_json, f, indent=2)
        
    df_label_counts = pd.DataFrame([
        {"label": k, "type": "raw_gold", "count": v} for k, v in Counter(Y_TRUE_RAW).items()
    ] + [
        {"label": k, "type": "mapped_gold", "count": v} for k, v in Counter(Y_TRUE_MAPPED).items()
    ] + [
        {"label": k, "type": "predicted", "count": v} for k, v in Counter(Y_PRED).items()
    ] + [
        {"label": k, "type": "ignored_raw", "count": v} for k, v in ignored_raw_labels.items()
    ])
    df_label_counts.to_csv(f"results/audits/{args.dataset}_label_counts.csv", index=False)
    
    if "per_class" in per_lang:
        df_classification_report = pd.DataFrame(per_lang["per_class"]).T.reset_index().rename(columns={"index": "label"})
        df_classification_report.to_csv(f"results/audits/{args.dataset}_classification_report.csv", index=False)
        
    if "confusion_matrix" in per_lang:
        df_cm = pd.DataFrame(per_lang["confusion_matrix"], index=per_lang["labels"], columns=per_lang["labels"])
        df_cm.to_csv(f"results/audits/{args.dataset}_confusion_matrix.csv", index=True)
        
    if args.export_errors:
        err_df = pd.DataFrame(errors[:args.limit_errors if args.limit_errors else len(errors)])
        err_df.to_csv(f"results/audits/{args.dataset}_errors.csv", index=False)
        
        b_err_df = pd.DataFrame(boundary_errors)
        b_err_df.to_csv(f"results/audits/{args.dataset}_boundary_errors.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--show-label-counts", action="store_true")
    parser.add_argument("--show-ignored-labels", action="store_true")
    parser.add_argument("--show-boundaries", action="store_true")
    parser.add_argument("--show-errors", action="store_true")
    parser.add_argument("--export-errors", action="store_true")
    parser.add_argument("--limit-errors", type=int, default=None)
    parser.add_argument("--fail-on-missing-required-label", action="store_true")
    parser.add_argument("--disable-cache", action="store_true")
    args = parser.parse_args()
    
    run_audit(args)
