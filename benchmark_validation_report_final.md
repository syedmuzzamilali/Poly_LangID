# PolyLID Benchmark Validation Report

## 1. Executive Summary

This report documents the final validation of the PolyLID benchmarking suite. The evaluation metrics have been fully audited and corrected to remove a severe macro-F1 contamination issue.

Previously, `sklearn.metrics` aggregated over the global 66-language inventory, treating zero-support classes (e.g., `zh`, `el` in a German-English dataset) as valid evaluation targets. This drastically skewed the macro-average downwards when the model produced noisy predictions for unrelated languages. The evaluation pipeline now enforces dataset-specific label validation, ensuring metrics are calculated only over languages structurally present in the specific dataset.

All results reported below are generated from a clean Git working tree and are fully reproducible using the authoritative benchmark runner.

## 2. Regression Testing and Code Integrity

The evaluation suite has been updated to use pure-Python metric calculation to bypass Windows DLL loading problems and `scikit-learn` version incompatibilities.

The test suite now includes 124 tests that verify:
- **Macro-F1 Validation**: Ensures zero-support labels are excluded.
- **Dataset Labels**: Prevents injection of unexpected labels.
- **Boundary Precision/Recall**: Uses character offsets mapped to token transition boundaries.
- **Result Export Integrity**: Validates non-negative counts, timezone-aware UTC timestamps, and correct CSV serialization structures.

All tests currently pass (124 passed, 0 skipped, 0 failed).

## 3. Final Overall Metrics

The global metrics across the 7 evaluated Code-Switching (CSW) datasets are as follows:

| Metric | Value | Definition |
| :--- | :--- | :--- |
| **Pooled Token Accuracy** | 89.58% | Total correct tokens / Total evaluated tokens across all datasets. |
| **Dataset Macro Token Accuracy** | 88.50% | Arithmetic mean of token accuracy per dataset. |
| **Dataset Macro F1** | 87.65% | Arithmetic mean of the corrected macro F1 per dataset. |
| **Combined Token Macro F1** | 89.10% | Macro F1 calculated over the concatenated array of all evaluated tokens. |
| **Combined Token Weighted F1** | 89.22% | Weighted F1 calculated over the concatenated array of all evaluated tokens. |
| **Overall Exact Match** | 46.88% | Proportion of sentences where the entire predicted label sequence perfectly matches the gold sequence. |
| **Overall Partial Match** | 85.31% | Mean sentence-level token agreement. |
| **Pooled Boundary F1** | 52.28% | F1 score over the sum of boundary True Positives, False Positives, and False Negatives across all datasets. |

### Note on Evaluation Strictness
- Exact Match requires *complete sequence equality*. A single token error drops the score for that sentence to 0.
- Boundary metrics require *exact positional agreement*. If PolyLID shifts a language boundary by a single token (often due to punctuation or subword alignment issues), it incurs both a False Positive and a False Negative. This strictness explains why Boundary F1 (52.28%) is notably lower than Token Accuracy (89.58%).

## 4. Dataset-Specific Observations

### 4.1 TongueSwitcher (German-English)
**Previous Macro-F1 (Contaminated):** 0.26
**Corrected Macro-F1:** 0.910
The massive discrepancy was caused by zero-support label aggregation. PolyLID performs exceptionally well at token classification on this dataset. The boundary metrics are lower (0.50 F1) because the exact token transition points sometimes drift, but the core language identification is highly accurate.

### 4.2 Turkish-German
**Previous Macro-F1 (Contaminated):** 0.617
**Corrected Macro-F1:** 0.926
The previous claim of a "severe class-level imbalance" was incorrect. Both Turkish and German exhibit strong precision and recall (F1 > 0.89). The poor macro-average was purely a metric implementation artifact.

### 4.3 Arabic-English
**Status:** Verified with limitation.
The token accuracy and macro-F1 remain lower on this dataset compared to others. PolyLID is an orthography-based model that relies heavily on script changes. The Arabic-English dataset contains a substantial amount of *Arabizi* (Arabic written in Latin script). PolyLID fundamentally struggles to distinguish Arabizi from English, leading to lowered recall for Arabic. This is a documented architectural limitation of the underlying `fastText` model.

## 5. Metadata and Provenance

- **Source Revision**: `a4a05d6735bdcfe7f9c0185ca4c332353c2f2257`
- **Execution Timestamp**: `2026-10-08T20:41:53.450720+00:00`
- **Working Tree Clean**: `True`

All result exports (`benchmark_results_final.csv`, `per_language_metrics.csv`) map to these exact execution parameters.
