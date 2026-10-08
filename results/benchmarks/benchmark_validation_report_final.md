# PolyLID Benchmark Validation Report

## Section 1: Reproducibility

- **Commit Hash**: `a4a05d6735bdcfe7f9c0185ca4c332353c2f2257`
- **Clean Working-Tree Status**: `True`
- **UTC Execution Timestamp**: `2026-10-08T20:41:53.450720+00:00`
- **Python Version**: 3.11.16
- **Operating System**: Windows
- **Model Versions**: `lid.176.ftz`
- **66-Language Inventory**: Configured and strictly audited
- **Test Count**: 124 tests
- **Artifact Paths**:
  - `results/benchmarks/benchmark_results_final.csv`
  - `results/benchmarks/per_language_metrics.csv`
  - `results/benchmarks/overall_metrics.json`
  - `results/benchmarks/combined_token_classification_report.csv`
  - `results/benchmarks/combined_token_confusion_matrix.csv`
  - `results/benchmarks/benchmark_validation_report_final.md`

## Section 2: Corrected metric definitions

Token accuracy is the proportion of evaluated tokens assigned the correct language label.

Macro F1 is the arithmetic mean of per-language F1 over the expected positive-support labels in each dataset.

Weighted F1 weights each per-language F1 by its support.

Exact Match is the proportion of sentences for which the complete predicted label sequence exactly matches the gold sequence.

Partial Match is the mean sentence-level token agreement. It gives each sentence equal weight.

Boundary precision, recall, and F1 are calculated from language-transition positions in the gold and predicted token-label sequences.

Unequal sequence lengths raise an error.

## Section 3: Evaluation defects corrected

The original Partial Match threshold was overly permissive.

German was incorrectly mapped to und in the original TongueSwitcher evaluation.

Zero-support labels contaminated the original macro-F1 calculations.

The final implementation validates expected dataset labels.

The corrected results were generated from a clean commit.

## Section 4: Arabic-English findings

The evaluated Arabic-English split contained 959 sentences and 10,998 gold tokens. After 911 ignored tokens were removed under the documented filtering rules, 10,087 tokens remained. PolyLID correctly classified 5,776 tokens, producing 57.26% token accuracy and 56.55% macro F1. Exact Match was 24.09%, mean sentence-level token agreement was 44.21%, and boundary F1 was 16.76%.

Arabic:
precision = 96.72%
recall = 45.75%
F1 = 62.12%
support = 7,726

English:
precision = 34.84%
recall = 94.92%
F1 = 50.97%
support = 2,361

Latin-script Arabic removes the script evidence available for native Arabic text. The current PolyLID configuration does not include a separate Arabizi or transliteration model, which contributes to reduced Arabic recall.

## Section 5: Overall results

Total sentences: 5,877
Total gold tokens: 135,993
Evaluated tokens: 126,224
Ignored tokens: 9,769
Correct tokens: 113,066

Pooled token accuracy: 89.58%
Dataset-macro token accuracy: 88.50%
Dataset-macro F1: 87.59%
Overall Exact Match: 46.88%
Overall Partial Match: 85.31%
Pooled boundary precision: 59.81%
Pooled boundary recall: 46.43%
Pooled boundary F1: 52.28%
Combined token-level macro F1: 89.10%
Combined token-level weighted F1: 89.22%

## Section 6: Dataset interpretation

Chinese-English has the strongest token and boundary results.
Arabic-English is limited by transliterated Arabic.
Indonesian-English has strong token performance and moderate boundary performance.
TongueSwitcher has strong token classification but low Exact Match and weaker boundary placement.
Turkish-German performs strongly for both German and Turkish.
LinCE Spanish-English has balanced per-language token performance but moderate boundary F1.
LinCE Turkish-English has strong Turkish performance and lower English recall.

## Section 7: Remaining limitations

- no separate Arabizi model;
- lower boundary performance on several same-script datasets;
- dataset-specific ignored labels;
- no completed component ablation yet;
- no completed threshold sweep yet;
- no complete hardware profiling yet.
