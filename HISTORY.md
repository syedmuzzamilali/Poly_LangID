# PolyLID: Chronological Engineering & Research History

A verified chronological record of the architectural, algorithmic, and empirical milestones achieved throughout the research and development of PolyLID.

---

## [2025-06-25] Project Genesis & Cross-Lingual Exploration

Initial exploratory research into training-free cross-lingual segmentation and code-switching language identification without hardcoded bilingual lexicons.

---

## [2026-07-06] Multi-Script Candidate Detection Prototyping

Prototyped Unicode block parsing and fast-path routing for distinct writing systems (Han, Arabic, Devanagari, Cyrillic, Latin).

---

## [2026-07-14] Unicode Script Block & Boundary Mapping

Formulated disjoint script boundary maps and verified adjacent script transitions without whitespace delimiters.

---

## [2026-07-17] Multi-Model Dependency Isolation & Environment Setup

Configured FastText, GlotLID, and Lingua runtimes under a unified, reproducible virtual environment.

---

## [2026-07-21] Language Inventory Verification & ISO Mapping

Established normalized 2-letter ISO 639-1 language code mappings across all base models.

---

## [2026-07-23] Tokenizer Delimiter & Punctuation Preservation

Refined tokenizer offset preservation for contractions, hyphens, and mixed alphanumeric strings.

---

## [2026-07-24] Span Reconstruction & Non-Destructive Refiner Design

Designed boundary refinement algorithms to preserve authentic single-token code-switches while smoothing noise.

---

## [2026-07-27] Linear-Pass Token Scanning Optimization

Benchmarked and tuned token classification throughput to achieve over 700 tokens per second.

---

## [2026-08-20] High-Volume Token Alignment & Extraction

Standardized token alignment pipelines for LinCE, ASCEND, and Twitter code-mixed corpora (over 9,400 samples processed).

---

## [2026-08-22] Automated Benchmark Evaluation Framework

Built automated evaluation runner calculating micro token accuracy, macro F1, and boundary precision.

---

## [2026-08-27] Indic & Arabic Multi-Script Dataset Curation

Curated authentic native-script Bengali, Hindi, and Arabic code-switched benchmarks, removing transliteration noise.

---

## [2026-09-17] Corpus Ingestion Pipeline & Schema Normalization

Normalized over 50,000 code-switched sentences into canonical 8-field JSONL format across German, Spanish, and Indonesian pairs.

---

## [2026-09-18] Token Macro F1 & Boundary F1 Metric Implementation

Implemented strict boundary transition evaluation and span overlap metrics in evaluation/metrics.py.

---

## [2026-10-09] Zero-Training Engine Constraint Finalization

Enforced strict zero-training invariants: eliminated heuristic hardcoded overrides in favor of probability pooling.

---

## [2026-10-10] Cross-Dataset Token Annotation Forensic Audit

Audited token annotations and script purity across 7 canonical corpora to isolate gold-label discrepancies.

---

