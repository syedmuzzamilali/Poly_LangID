import re

with open('polylid_eval.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "    boundary_f1: float\n    span_exact: float",
    "    boundary_f1: float\n    exact_match: float\n    partial_match: float\n    span_exact: float"
)

text = text.replace(
    "    boundary_tp = boundary_fp = boundary_fn = 0\n    span_exact_total = 0",
    "    boundary_tp = boundary_fp = boundary_fn = 0\n    exact_match_hits = 0\n    partial_match_hits = 0\n    total_sentences = 0\n    span_exact_total = 0"
)

text = text.replace(
    "            if not gold_tags: continue\n            acc = accuracy_score(gold_tags, pred_tags)\n            cmi = calculate_cmi(gold_tags)",
    "            if not gold_tags: continue\n            acc = accuracy_score(gold_tags, pred_tags)\n            if acc == 1.0:\n                exact_match_hits += 1\n            if acc >= 0.5:\n                partial_match_hits += 1\n            total_sentences += 1\n            cmi = calculate_cmi(gold_tags)"
)

text = text.replace(
    "    span_exact = span_exact_hit / max(1, span_exact_total)",
    "    exact_match = exact_match_hits / max(1, total_sentences)\n    partial_match = partial_match_hits / max(1, total_sentences)\n    span_exact = span_exact_hit / max(1, span_exact_total)"
)

text = text.replace(
    "        boundary_f1=boundary_f1,\n        span_exact=span_exact,",
    "        boundary_f1=boundary_f1,\n        exact_match=exact_match,\n        partial_match=partial_match,\n        span_exact=span_exact,"
)

text = text.replace(
    "        \"boundary_f1\": r.boundary_f1,\n        \"span_exact\": r.span_exact,",
    "        \"boundary_f1\": r.boundary_f1,\n        \"exact_match\": r.exact_match,\n        \"partial_match\": r.partial_match,\n        \"span_exact\": r.span_exact,"
)

text = text.replace(
    "            \"boundary_f1\": r.boundary_f1,\n            \"span_exact\": r.span_exact,",
    "            \"boundary_f1\": r.boundary_f1,\n            \"exact_match\": r.exact_match,\n            \"partial_match\": r.partial_match,\n            \"span_exact\": r.span_exact,"
)

text = text.replace(
    "        \"macro_f1\": r.token_macro_f1,\n        \"boundary_f1\": r.boundary_f1,\n        \"latency_ms\"",
    "        \"macro_f1\": r.token_macro_f1,\n        \"boundary_f1\": r.boundary_f1,\n        \"exact_match\": r.exact_match,\n        \"partial_match\": r.partial_match,\n        \"latency_ms\""
)

text = text.replace(
    "            \"weighted_f1\": r.token_weighted_f1,\n            \"boundary_f1\": r.boundary_f1,\n",
    "            \"weighted_f1\": r.token_weighted_f1,\n            \"boundary_f1\": r.boundary_f1,\n            \"exact_match\": r.exact_match,\n            \"partial_match\": r.partial_match,\n"
)

text = text.replace(
    "for r in results:\n        print(r.name, \"macro_f1=\", round(r.token_macro_f1, 4), \"token_acc=\", round(r.token_acc, 4), \"boundary_f1=\", round(r.boundary_f1, 4))",
    "for r in results:\n        print(r.name, \"macro_f1=\", round(r.token_macro_f1, 4), \"token_acc=\", round(r.token_acc, 4), \"boundary_f1=\", round(r.boundary_f1, 4), \"EM=\", round(r.exact_match, 4), \"PM=\", round(r.partial_match, 4))"
)

with open('polylid_eval.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Patched polylid_eval.py')
