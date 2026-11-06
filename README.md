# PolyLID: High-Throughput, Training-Free Code-Switching Language Identification

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-155%20Passed-brightgreen.svg)]()
[![Throughput](https://img.shields.io/badge/Throughput-~1%2C000%20tokens%2Fsec-orange.svg)]()
[![Philosophy](https://img.shields.io/badge/Philosophy-Zero%20Training%20%7C%20Zero%20Hardcoding-purple.svg)]()

**PolyLID** is an unsupervised, high-throughput sequence segmentation engine for **code-switching language identification (CS-LID)**. It identifies language transitions at the token and span level across multilingual, intra-sentential code-mixed text without requiring any model training, fine-tuning, or pair-specific hardcoded lexicons.

---

## 🌟 Key Features & Core Philosophy

* **Fine-Grained Token & Span Resolution**: Predicts exact word-level language tags and continuous `(start_char, end_char, lang)` spans with boundary detection.
* **Strict Zero-Training Architecture**: Operates purely via unsupervised consensus arbitration over off-the-shelf base models (FastText, GlotLID, and Lingua). No parameters are trained or fine-tuned.
* **Zero Hardcoded Pair Rules**: Completely language-agnostic. No pair-specific bilingual lexicons, regex lists, or hardcoded exception dictionaries.
* **High Production Throughput**: Processes streams at **~1,000 tokens/second** in a single linear pass.
* **Broad Typological Coverage**: Validated across 9 corpora covering 7 distinct script and morphological topologies (isolating, fusional, agglutinative, root-pattern, disjoint scripts).

---

## 📊 Benchmark Results

### 1. Master Evaluation Benchmark (All 9 Corpora)
Evaluated with the authoritative PolyLID multi-tiered pipeline:

| Dataset | Language Pair / Topology | Evaluated Tokens | Token Accuracy (%) | Sentence Exact Match (%) | Boundary F1 (%) | Throughput (tok/s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **ASCEND** | Chinese-English *(Disjoint Scripts)* | 10,225 | **98.28%** | **89.20%** | **95.18%** | 907 |
| **Sabty Clean** | Arabic Native / Mixed *(Mixed Scripts)* | 9,573 | **96.33%** | **72.31%** | **60.71%** | 1,070 |
| **DE-EN Standard**| German-English Standard *(Fusional)* | 14,706 | **96.82%** | **71.92%** | **48.61%** | 922 |
| **LinCE Spa-Eng** | Spanish-English *(Romance-Germanic)* | 8,279 | **95.16%** | **72.77%** | **55.84%** | 969 |
| **Bilingual Tweets**| Turkish-German *(Agglutinative-Fusional)*| 9,162 | **90.79%** | **44.56%** | **63.86%** | 937 |
| **LinCE Tur-Eng** | Turkish-English *(Agglutinative-Germanic)*| 5,142 | **91.64%** | **38.46%** | **66.80%** | 989 |
| **Twitter CS** | Indonesian-English *(Colloquial Isolating)*| 16,392 | **89.38%** | **26.94%** | **51.24%** | 878 |
| **TongueSwitcher**| DE-EN *(Long Paragraphs, 69 tok/sent)* | 66,545 | **91.69%** | **13.41%** | **38.27%** | 1,017 |
| **Historical Arabizi**| Arabic-English *(Latin Transliterated)* | 10,365 | *58.20%* | *23.57%* | *18.88%* | 1,638 |

*(Full benchmark logs stored in `results/extended_benchmark_results.csv`)*

---

### 2. PolyLID vs. MaskLID (ACL 2024 SOTA)

MaskLID (Kargaran, Yvon, Schütze, *ACL 2024*, arXiv:2406.06263) is the published training-free baseline for code-switching.

| Dimension | **MaskLID** (ACL 2024) | **PolyLID** (Our Work) |
| :--- | :--- | :--- |
| **Task Formulation** | Sentence-level multi-label set (`{'tr', 'en'}`) | **Token-level sequence labeling + character spans** |
| **Span Localization** | ❌ None (no character offsets) | ✅ **Full character spans `(start, end, lang)`** |
| **Boundary Detection** | ❌ None (cannot locate switch points) | ✅ **Evaluated Boundary F1: 55.8% to 95.2%** |
| **Single-Word Switches**| ❌ Discarded / Fails if $\le 20\text{--}25$ bytes | ✅ **Detects 1-word and 1-character switches** |
| **Turkish-English** | Detected only 91 / 372 CS sents (**24.5% recall**) | **91.64% Token Acc**, **38.46% Full-Sentence EM** |
| **Spanish-English** | Tested Basque-Spanish: 47 / 1377 (**3.4% recall**) | **95.16% Token Acc**, **72.77% Full-Sentence EM** |
| **Inference Latency** | Iterative multi-pass masking loop ($\lambda \ge 2$) | **Single-pass streaming: ~1,000 tokens/sec** |

---

## 🚀 Quickstart

### 1. Installation

Clone repository and install dependencies:

```bash
git clone https://github.com/your-username/prmtblids.git
cd prmtblids
pip install -r requirements.txt
```

### 2. Python API

```python
from polylid import PolyLIDPipeline

# Initialize detector
detector = PolyLIDPipeline()

# Input mixed text
text = "Buenos dias my friend, I hope you have a great day hoy!"

# Detect continuous spans
spans = detector.detect_languages(text)
print(spans)
# Output: [('Buenos dias ', 'es'), ('my friend, I hope you have a great day ', 'en'), ('hoy!', 'es')]
```

### 3. Command Line Interface (CLI)

```bash
# Analyze any text directly from terminal
python polylid.py "Kaixo lagunak, cómo están hoy? Oso ondo nago."

# Optionally restrict candidate set
python polylid.py "parti'ye gittik very nice" --allowed tr en
```

### 4. Interactive Web Application

Launch the built-in Flask academic workbench:

```bash
python webapp/app.py
```
Open your browser at `http://127.0.0.1:5000` to interactively visualize token boundaries, confidence distributions, and decision traces.

---

## 🧪 Evaluation & Reproduction

Run the complete 155-test verification suite:
```bash
pytest -p no:anyio tests/
```

Reproduce the master multi-corpus evaluation:
```bash
python evaluation/run_e4_ow_reproduction.py
```

---

## 📁 Repository Layout

```
prmtblids/
├── polylid.py                             # Core PolyLID Pipeline Engine & CLI
├── polylid_eval.py                        # Evaluation & Diagnostic Engine
├── requirements.txt                       # Python dependencies
├── pytest.ini                             # Pytest configuration
│
├── webapp/                                # Academic Web Application (Flask UI)
│   ├── app.py                             # Web server & API
│   ├── templates/                         # Interactive HTML templates
│   └── static/                            # Stylesheets & JavaScript
│
├── datasets/                              # All 9 Evaluated Corpora (LinCE, ASCEND, etc.)
├── evaluation/                            # Evaluation scripts, ablations, and metrics
├── results/                               # Authoritative benchmark CSVs and tables
├── tests/                                 # Unit test suite (155 passing tests)
├── manifests/                             # Evaluation integrity manifests
│
├── thesis_benchmark_tables.md             # Master benchmark tables for thesis/paper
├── PolyBench_Report.html                  # Visual diagnostic report
└── drop/                                  # Archive of scratch scripts & background PDFs
```

---

## 📜 Citation

If you use PolyLID in your research, please cite:

```bibtex
@article{polylid2026,
  title={PolyLID: High-Throughput, Training-Free Code-Switching Language Identification across Diverse Script Typologies},
  author={Takweer, et al.},
  journal={arXiv preprint},
  year={2026}
}
```
