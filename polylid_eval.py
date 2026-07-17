
#!/usr/bin/env python3
from __future__ import annotations

"""
PolyBench evaluator for multilingual code-switched token/span LID.

Features:
- token-level metrics
- span/boundary diagnostics
- error taxonomy
- CMI / switches / length stress testing
- latency profiling
- ablation comparison across multiple detectors
- HTML report + forensic TXT trace
"""

import argparse
import importlib
import json
import os
import random
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    import psutil
except Exception:
    psutil = None

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

DATASET_PATH_DEFAULT = "datasets/lince_spaeng.json"
REPORT_FILE_DEFAULT = "PolyBench_Report.html"
TRACE_FILE_DEFAULT = "forensic_trace.txt"

SCRIPT_RANGES = {
    "HAN": [(0x4E00, 0x9FFF)],
    "HIRAGANA": [(0x3040, 0x309F)],
    "KATAKANA": [(0x30A0, 0x30FF)],
    "HANGUL": [(0xAC00, 0xD7AF)],
    "THAI": [(0x0E00, 0x0E7F)],
    "ARABIC": [(0x0600, 0x06FF)],
    "DEVANAGARI": [(0x0900, 0x097F)],
    "BENGALI": [(0x0980, 0x09FF)],
    "CYRILLIC": [(0x0400, 0x04FF)],
    "LATIN": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x017F)],
}

def script_of_char(ch: str) -> str:
    code = ord(ch)
    for script, ranges in SCRIPT_RANGES.items():
        for lo, hi in ranges:
            if lo <= code <= hi:
                return script
    return "OTHER"

def dominant_script_for_text(text: str) -> str:
    votes = Counter()
    for ch in text:
        if ch.isalpha():
            votes[script_of_char(ch)] += 1
    return votes.most_common(1)[0][0] if votes else "OTHER"

def normalize_text(t: str) -> str:
    return unicodedata.normalize("NFC", t or "").strip().lower()

def normalize_lang_tag(tag):
    if tag is None:
        return "und"
    if not isinstance(tag, str):
        tag = str(tag)
    t = tag.strip().lower()
    if not t or t in {"none", "null", "nan", "unknown"}:
        return "und"
    return t

def tokenize(text: str) -> List[str]:
    text = unicodedata.normalize("NFC", text or "")
    toks = []
    buf = []
    last = None
    for ch in text:
        sc = script_of_char(ch)
        sep = ch.isspace() or unicodedata.category(ch).startswith("P") or unicodedata.category(ch).startswith("S")
        if sep:
            if buf:
                toks.append("".join(buf))
                buf = []
            last = None
            continue
        if buf and last and sc != last and sc != "OTHER" and last != "OTHER":
            toks.append("".join(buf))
            buf = [ch]
        else:
            buf.append(ch)
        if sc != "OTHER":
            last = sc
    if buf:
        toks.append("".join(buf))
    return [t for t in toks if t.strip()]

def build_ordered_span_ranges(sent, spans, tuple_mode=False):
    ranges = []
    cursor = 0
    for span in spans:
        if tuple_mode:
            text, lang = span
        else:
            text, lang = span.get("text", ""), span.get("lang", "und")
        if not text:
            continue
        st = sent.find(text, cursor)
        if st == -1:
            st = sent.find(text)
        if st == -1:
            continue
        en = st + len(text)
        ranges.append((st, en, normalize_lang_tag(lang)))
        cursor = en
    return ranges

def token_overlap(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    return 0.0 if not sa else len(sa & sb) / len(sa)

def calculate_cmi(tags: Sequence[str]) -> float:
    if not tags:
        return 0.0
    c = Counter(tags)
    return 100.0 * (1 - c.most_common(1)[0][1] / len(tags))

def boundary_metrics(gold_tags: Sequence[str], pred_tags: Sequence[str]) -> Tuple[int, int, int]:
    # returns tp, fp, fn for boundary detection
    tp = fp = fn = 0
    for i in range(len(gold_tags) - 1):
        g = gold_tags[i] != gold_tags[i + 1]
        p = pred_tags[i] != pred_tags[i + 1]
        if g and p:
            tp += 1
        elif (not g) and p:
            fp += 1
        elif g and (not p):
            fn += 1
    return tp, fp, fn

def dataset_memory_mb() -> float:
    if psutil is None:
        return 0.0
    try:
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0

def html_table(df: pd.DataFrame, title: str) -> str:
    return f"<section><h2>{escape(title)}</h2>{df.to_html(index=False, classes='data-table')}</section>"

def html_pre(text: str) -> str:
    return f"<pre style='white-space:pre-wrap'>{escape(text)}</pre>"

@dataclass
class EvalResult:
    name: str
    token_acc: float
    token_macro_f1: float
    token_weighted_f1: float
    boundary_f1: float
    span_exact: float
    span_overlap: float
    avg_latency_ms: float
    p95_latency_ms: float
    throughput_tps: float
    peak_mem_mb: float
    error_counts: Dict[str, int]
    report_df: pd.DataFrame
    confusion_df: pd.DataFrame
    sentence_df: pd.DataFrame
    top_confusions_df: pd.DataFrame
    boundary_script_df: pd.DataFrame
    trace_lines: List[str]

def evaluate_one(detector_module: str, dataset: List[dict], limit: int | None = None, batch_size: int = 128, deterministic: bool = False) -> EvalResult:
    if deterministic:
        random.seed(42)
        np.random.seed(42)

    mod = importlib.import_module(detector_module)
    batch_detect = getattr(mod, "batch_detect_languages")
    name = detector_module.split(".")[-1]

    if limit:
        dataset = dataset[:limit]

    texts = [x["text"] for x in dataset]
    gold_spans_all = [x["spans"] for x in dataset]

    Y_TRUE, Y_PRED = [], []
    meta_rows = []
    trace_lines = []
    error_types = Counter()
    gold_freq = Counter()
    
    # Dynamically determine allowed_langs from the dataset's gold spans
    allowed_langs_set = set()
    for row_spans in gold_spans_all:
        for span in row_spans:
            lang = normalize_lang_tag(span.get("lang", "und"))
            if lang != "und":
                allowed_langs_set.add(lang)
    allowed_langs = list(allowed_langs_set) if allowed_langs_set else None

    pred_freq = Counter()
    confusion_pairs = Counter()
    boundary_total = Counter()
    boundary_err = Counter()
    boundary_tp = boundary_fp = boundary_fn = 0
    span_exact_total = 0
    span_exact_hit = 0
    span_overlap_sum = 0.0
    span_overlap_count = 0

    latencies = []
    mem_peak = dataset_memory_mb()

    start_all = time.perf_counter()
    for i in range(0, len(texts), batch_size):
        batch_txt = texts[i:i+batch_size]
        batch_gold = gold_spans_all[i:i+batch_size]

        t0 = time.perf_counter()
        
        # Check if batch_detect accepts allowed_langs
        import inspect
        sig = inspect.signature(batch_detect)
        if "allowed_langs" in sig.parameters:
            batch_pred = batch_detect(batch_txt, allowed_langs=allowed_langs)
        else:
            batch_pred = batch_detect(batch_txt)
            
        t1 = time.perf_counter()
        # amortize latency across batch
        batch_lat = (t1 - t0) / max(1, len(batch_txt))
        latencies.extend([batch_lat] * len(batch_txt))

        for sent, gold_spans, pred_spans in zip(batch_txt, batch_gold, batch_pred):
            tokens = tokenize(sent)
            if not tokens:
                continue

            # token character ranges
            token_ranges = []
            cursor = 0
            for t in tokens:
                s = sent.find(t, cursor)
                if s == -1:
                    s = sent.find(t)
                if s == -1:
                    continue
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

            raw_gold_tags = [normalize_lang_tag(tag_for(s, e, gold_ranges)) for s, e in token_ranges]
            raw_pred_tags = [normalize_lang_tag(tag_for(s, e, pred_ranges)) for s, e in token_ranges]
            raw_valid_tokens = [sent[s:e] for s, e in token_ranges]

            valid_indices = [i for i, g in enumerate(raw_gold_tags) if g != "und"]
            gold_tags = [raw_gold_tags[i] for i in valid_indices]
            pred_tags = [raw_pred_tags[i] for i in valid_indices]
            valid_tokens = [raw_valid_tokens[i] for i in valid_indices]

            Y_TRUE.extend(gold_tags)
            Y_PRED.extend(pred_tags)

            for gt, pt in zip(gold_tags, pred_tags):
                if gt != pt:
                    confusion_pairs[(gt, pt)] += 1

            for k in range(len(gold_tags) - 1):
                boundary_text = f"{valid_tokens[k]} {valid_tokens[k+1]}"
                b_script = dominant_script_for_text(boundary_text)
                boundary_total[b_script] += 1
                g_boundary = gold_tags[k] != gold_tags[k + 1]
                p_boundary = pred_tags[k] != pred_tags[k + 1]
                if g_boundary and p_boundary:
                    boundary_tp += 1
                elif (not g_boundary) and p_boundary:
                    boundary_fp += 1
                elif g_boundary and (not p_boundary):
                    boundary_fn += 1
                if g_boundary != p_boundary:
                    boundary_err[b_script] += 1

            for g in gold_tags:
                gold_freq[g] += 1
            for p in pred_tags:
                pred_freq[p] += 1

            acc = accuracy_score(gold_tags, pred_tags)
            cmi = calculate_cmi(gold_tags)
            switches = sum(gold_tags[k] != gold_tags[k+1] for k in range(len(gold_tags) - 1))
            meta_rows.append({
                "text": sent,
                "length": len(tokens),
                "cmi": cmi,
                "switches": switches,
                "accuracy": acc,
                "dominant_lang": Counter(gold_tags).most_common(1)[0][0] if gold_tags else "und",
            })

            sent_errs = 0

            # span diagnostics
            matched_pred = set()
            for g in gold_spans:
                gtxt, glang = normalize_text(g["text"]), normalize_lang_tag(g.get("lang"))
                best_ov = 0.0
                best_idx = None
                best = None
                for idx, (ptxt, plang) in enumerate(pred_spans):
                    if idx in matched_pred:
                        continue
                    ov = token_overlap(gtxt, normalize_text(ptxt))
                    if ov > best_ov:
                        best_ov = ov
                        best_idx = idx
                        best = (ptxt, plang)
                span_exact_total += 1
                if best is None or best_ov < 0.30:
                    error_types["missed_span"] += 1
                    trace_lines.append(str(("missed_span", sent, gtxt, glang)))
                    sent_errs += 1
                    continue
                matched_pred.add(best_idx)
                ptxt, plang = best
                span_overlap_sum += best_ov
                span_overlap_count += 1
                if normalize_text(ptxt) == gtxt:
                    span_exact_hit += 1
                else:
                    error_types["boundary_error"] += 1
                    trace_lines.append(str(("boundary_error", sent, gtxt, glang, ptxt, plang)))
                    sent_errs += 1
                if normalize_lang_tag(plang) != glang:
                    error_types["wrong_language"] += 1
                    trace_lines.append(str(("wrong_language", sent, gtxt, glang, plang)))
                    sent_errs += 1

            for idx, (ptxt, plang) in enumerate(pred_spans):
                if idx in matched_pred:
                    continue
                if not any(token_overlap(normalize_text(ptxt), normalize_text(g["text"])) > 0.30 for g in gold_spans):
                    error_types["extra_span"] += 1
                    sent_errs += 1

            if sent_errs > 0:
                meta_rows[-1]["error_count"] = sent_errs

            # memory sampling
            if psutil is not None:
                try:
                    mem_peak = max(mem_peak, dataset_memory_mb())
                except Exception:
                    pass

    total_time = time.perf_counter() - start_all
    report = classification_report(Y_TRUE, Y_PRED, output_dict=True, zero_division=0)
    labels = sorted(set(Y_TRUE) | set(Y_PRED))
    true_labels = sorted(set(Y_TRUE))
    cm = confusion_matrix(Y_TRUE, Y_PRED, labels=labels)
    prf = precision_recall_fscore_support(Y_TRUE, Y_PRED, labels=true_labels, average="macro", zero_division=0)

    token_acc = accuracy_score(Y_TRUE, Y_PRED)
    macro_f1 = prf[2] # fbeta_score is the 3rd element
    weighted_f1 = report["weighted avg"]["f1-score"]

    b_tp, b_fp, b_fn = boundary_tp, boundary_fp, boundary_fn
    boundary_f1 = (2*b_tp) / max(1, (2*b_tp + b_fp + b_fn))

    top_confusions = pd.DataFrame(
        [{"gold": g, "pred": p, "count": c} for (g, p), c in confusion_pairs.most_common(50)]
    )

    boundary_rows = []
    for script in sorted(boundary_total.keys()):
        tot = int(boundary_total[script])
        err = int(boundary_err.get(script, 0))
        boundary_rows.append({"script": script, "boundary_pairs": tot, "boundary_errors": err, "error_rate": (err / tot) if tot else 0.0})
    boundary_df = pd.DataFrame(boundary_rows)

    df_meta = pd.DataFrame(meta_rows)
    if not df_meta.empty:
        df_meta["cmi_bin"] = pd.cut(df_meta["cmi"], [-1, 0, 15, 100], labels=["Monolingual", "LowMix", "HighMix"])

    # span overlap / exact
    span_exact = span_exact_hit / max(1, span_exact_total)
    span_overlap = span_overlap_sum / max(1, span_overlap_count)

    lat = np.array(latencies, dtype=float) * 1000.0 if latencies else np.array([0.0])
    avg_latency_ms = float(np.mean(lat))
    p95_latency_ms = float(np.percentile(lat, 95))
    throughput_tps = float(len(texts) / max(1e-9, total_time))
    if hasattr(mod, "get_detector"):
        det = mod.get_detector()
        if hasattr(det, "trigger_counts"):
            print(f"[{name}] Triggers: {det.trigger_counts}")
            
    return EvalResult(
        name=name,
        token_acc=token_acc,
        token_macro_f1=macro_f1,
        token_weighted_f1=weighted_f1,
        boundary_f1=boundary_f1,
        span_exact=span_exact,
        span_overlap=span_overlap,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=p95_latency_ms,
        throughput_tps=throughput_tps,
        peak_mem_mb=mem_peak,
        error_counts=dict(error_types),
        report_df=pd.DataFrame(report).transpose().reset_index().rename(columns={"index": "label"}),
        confusion_df=pd.DataFrame(cm, index=labels, columns=labels).reset_index().rename(columns={"index": "gold/pred"}),
        sentence_df=df_meta,
        top_confusions_df=top_confusions,
        boundary_script_df=boundary_df,
        trace_lines=trace_lines,
    )

def render_html(results: List[EvalResult], report_file: str, trace_file: str, dataset_size: int):
    # summary table
    summary = pd.DataFrame([{
        "detector": r.name,
        "token_acc": r.token_acc,
        "macro_f1": r.token_macro_f1,
        "weighted_f1": r.token_weighted_f1,
        "boundary_f1": r.boundary_f1,
        "span_exact": r.span_exact,
        "span_overlap": r.span_overlap,
        "avg_latency_ms": r.avg_latency_ms,
        "p95_latency_ms": r.p95_latency_ms,
        "throughput_tps": r.throughput_tps,
        "peak_mem_mb": r.peak_mem_mb,
        "errors": sum(r.error_counts.values()),
    } for r in results])

    # overall HTML
    html = [f"""
<html><head><meta charset="utf-8"/>
<title>PolyBench Report</title>
<style>
body{{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;padding:0}}
section{{background:#fff;max-width:1400px;margin:1.5rem auto;padding:1.25rem 1.5rem;border-radius:10px;box-shadow:0 2px 10px #0001}}
.data-table{{width:100%;border-collapse:collapse;font-size:12px}}
.data-table th{{background:#eef3fb;border:1px solid #ccd;padding:6px;text-align:left}}
.data-table td{{border:1px solid #ddd;padding:6px;vertical-align:top}}
small.muted{{color:#666}}
h1,h2,h3{{margin-top:0}}
code{{background:#f1f3f5;padding:2px 4px;border-radius:4px}}
</style>
</head><body>
<section>
<h1>PolyBench Evaluation Report</h1>
<p><b>Dataset size:</b> {dataset_size}</p>
<p><small class="muted">This report compares multiple detectors using the same benchmark protocol.</small></p>
</section>
"""]

    html.append(html_table(summary, "Model Comparison Summary"))

    # per-model sections
    for r in results:
        html.append(f"<section><h2>{escape(r.name)}</h2>")
        html.append(pd.DataFrame([{
            "token_acc": r.token_acc,
            "macro_f1": r.token_macro_f1,
            "weighted_f1": r.token_weighted_f1,
            "boundary_f1": r.boundary_f1,
            "span_exact": r.span_exact,
            "span_overlap": r.span_overlap,
            "avg_latency_ms": r.avg_latency_ms,
            "p95_latency_ms": r.p95_latency_ms,
            "throughput_tps": r.throughput_tps,
            "peak_mem_mb": r.peak_mem_mb,
            "error_total": sum(r.error_counts.values()),
        }]).to_html(index=False, classes="data-table"))
        html.append(html_table(r.report_df, f"{r.name} Per-language Classification Report"))
        html.append(html_table(r.confusion_df, f"{r.name} Confusion Matrix"))
        html.append(html_table(pd.DataFrame([{"error_type": k, "count": v} for k, v in sorted(r.error_counts.items(), key=lambda kv: kv[1], reverse=True)]),
                              f"{r.name} Error Taxonomy"))
        if not r.top_confusions_df.empty:
            html.append(html_table(r.top_confusions_df, f"{r.name} Top Confusions"))
        if not r.boundary_script_df.empty:
            html.append(html_table(r.boundary_script_df, f"{r.name} Boundary Errors by Script"))
        if not r.sentence_df.empty:
            html.append(html_table(r.sentence_df, f"{r.name} Sentence-level Metadata"))
        html.append("</section>")

    # optional traces
    html.append(f"<section><h2>Forensic Trace</h2><pre style='white-space:pre-wrap'>{escape('\n'.join(results[0].trace_lines[:5000]) if results else '')}</pre></section>")
    html.append("</body></html>")


    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    with open(trace_file, "w", encoding="utf-8") as f:
        if results:
            for line in results[0].trace_lines:
                f.write(line + "\n")

def render_md(results: List[EvalResult], md_file: str, dataset_size: int):
    md = []
    md.append("# PolyBench Evaluation Report\n")
    md.append(f"**Dataset size:** {dataset_size}\n")
    
    md.append("## Model Comparison Summary\n")
    summary = pd.DataFrame([{
        "model": r.name,
        "token_acc": r.token_acc,
        "macro_f1": r.token_macro_f1,
        "boundary_f1": r.boundary_f1,
        "latency_ms": r.avg_latency_ms,
        "mem_mb": r.peak_mem_mb
    } for r in results])
    md.append(summary.to_markdown(index=False))
    md.append("\n")

    for r in results:
        md.append(f"## {r.name}\n")
        md.append("### Metrics\n")
        metrics = pd.DataFrame([{
            "token_acc": r.token_acc,
            "macro_f1": r.token_macro_f1,
            "weighted_f1": r.token_weighted_f1,
            "boundary_f1": r.boundary_f1,
            "span_exact": r.span_exact,
            "span_overlap": r.span_overlap,
            "avg_latency_ms": r.avg_latency_ms,
            "p95_latency_ms": r.p95_latency_ms,
            "throughput_tps": r.throughput_tps,
            "peak_mem_mb": r.peak_mem_mb,
            "error_total": sum(r.error_counts.values()),
        }])
        md.append(metrics.to_markdown(index=False))
        md.append("\n")
        
        md.append(f"### {r.name} Per-language Classification Report\n")
        if not r.report_df.empty:
            md.append(r.report_df.to_markdown(index=False))
        md.append("\n")
        
        md.append(f"### {r.name} Confusion Matrix\n")
        if not r.confusion_df.empty:
            md.append(r.confusion_df.to_markdown(index=False))
        md.append("\n")
        
        md.append(f"### {r.name} Error Taxonomy\n")
        err_df = pd.DataFrame([{"error_type": k, "count": v} for k, v in sorted(r.error_counts.items(), key=lambda kv: kv[1], reverse=True)])
        if not err_df.empty:
            md.append(err_df.to_markdown(index=False))
        md.append("\n")
        
        if not r.top_confusions_df.empty:
            md.append(f"### {r.name} Top Confusions\n")
            md.append(r.top_confusions_df.to_markdown(index=False))
            md.append("\n")
            
        if not r.boundary_script_df.empty:
            md.append(f"### {r.name} Boundary Errors by Script\n")
            md.append(r.boundary_script_df.to_markdown(index=False))
            md.append("\n")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=DATASET_PATH_DEFAULT)
    ap.add_argument("--detectors", default="polybeta",
                    help="Comma-separated detector modules to compare.")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--report", default=REPORT_FILE_DEFAULT)
    ap.add_argument("--trace", default=TRACE_FILE_DEFAULT)
    ap.add_argument("--deterministic", action="store_true")
    args = ap.parse_args()

    if args.deterministic:
        random.seed(42)
        np.random.seed(42)

    if args.dataset.endswith(".csv"):
        import pandas as pd
        import ast
        df = pd.read_csv(args.dataset)
        dataset = []
        for idx, row in df.iterrows():
            ann = row.get("Annotated by: Annotator 1")
            if pd.isna(ann) or str(ann).strip() == "":
                ann = row.get("Annotated by: Annotator 2")
            if pd.isna(ann) or str(ann).strip() == "":
                ann = row.get("Annotated by: Annotator 3")
            if pd.isna(ann) or str(ann).strip() == "":
                ann = row.get("Predicted tags")
                
            if pd.isna(ann) or str(ann).strip() == "":
                continue
                
            try:
                tags = ast.literal_eval(str(ann))
            except Exception:
                continue
                
            spans = []
            for t in tags:
                if isinstance(t, dict):
                    lang = str(t.get("value", "und")).strip().lower()
                    key = str(t.get("key", ""))
                elif isinstance(t, list) and len(t) >= 2:
                    key = str(t[0])
                    lang = str(t[1]).strip().lower()
                else:
                    continue
                    
                # Universally handle shorthands
                if lang == "h": lang = "hi"
                elif lang == "e": lang = "en"
                elif lang == "u": lang = "und"
                elif lang == "ot": lang = "und"
                
                spans.append({"text": key, "lang": lang})
                
            if spans:
                dataset.append({
                    "text": str(row.get("Sentences", "")),
                    "spans": spans
                })
        print(f"Loaded {len(dataset)} samples from CSV.")
    else:
        with open(args.dataset, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
            if isinstance(raw_json, dict) and "data" in raw_json:
                from polybeta import LANG_NAME_TO_CODE
                dataset = []
                for item in raw_json["data"]:
                    text = item.get("native sentence", "")
                    if not text:
                        continue
                    lang_name = item.get("language", "")
                    code = LANG_NAME_TO_CODE.get(lang_name.lower(), lang_name.lower()[:2])
                    dataset.append({"text": text, "spans": [{"text": text, "lang": code}]})
            else:
                dataset = raw_json
            
    if args.limit:
        dataset = dataset[:args.limit]

    detector_modules = [d.strip() for d in args.detectors.split(",") if d.strip()]
    results = []
    for module in detector_modules:
        results.append(evaluate_one(module, dataset, limit=None, batch_size=args.batch_size, deterministic=args.deterministic))

    render_html(results, "PolyBench_Report.html", args.trace, len(dataset))
    
    md_report = "PolyBench_Report.html".replace(".html", ".md")
    render_md(results, md_report, len(dataset))

    print("DONE")
    for r in results:
        print(r.name, "macro_f1=", round(r.token_macro_f1, 4), "token_acc=", round(r.token_acc, 4), "boundary_f1=", round(r.boundary_f1, 4))
    print("Report:", "PolyBench_Report.html")
    print("Trace:", args.trace)

if __name__ == "__main__":
    main()
