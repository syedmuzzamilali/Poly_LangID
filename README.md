# PolyBeta V5: Context-First Hierarchical Language Identification

**PolyBeta V5 (Polylid)** is an advanced, token-level language identification (LID) framework specifically designed for multilingual and code-switched text. It introduces a novel **Context-First Hierarchical State-Transition Framework** that resolves the traditional pitfalls of token-level classifiers by replacing unconstrained language inventories with a strict, three-level contextual hierarchy.

## Overview

Conventional token-level classifiers suffer from severe precision degradation when exposed to open-vocabulary search, struggling with lexical overlap, homographs, proper nouns, and short interjections. PolyBeta V5 solves this by dynamically constraining the candidate space *before* classifying individual tokens.

### The Three-Level Hierarchy

1. **Level 1: Global Sentence Discovery (State-Transition Iteration)**
   An algorithmic masked discovery process iterates over the sentence to extract a precise candidate language set. At each iteration, newly discovered languages are accumulated, and their lexical contribution is masked from the remaining sentence. This deterministically reduces the downstream candidate search space by **6.1× to 13.0×**.

2. **Level 2: Restricted Candidate Token Classification**
   Specialized statistical subword and lexical models evaluate each token *strictly* within the discovered candidate set, mathematically eliminating out-of-candidate false positive confusions.

3. **Level 3: Boundary Analysis & Local Context Refinement**
   Instead of applying blunt spatial smoothing heuristics across entire sentences, the framework performs selective **Local Phrase Context Refinement**. It expands left and right up to script boundaries to collect linguistic evidence for low-margin or conflicting token classifications before making a final arbitration decision.

## Performance & State-of-the-Art Results

We evaluated PolyBeta V5 across standard LinCE code-switching benchmarks (`lince_spaeng`, `lince_turen`) alongside multi-script bilingual and trilingual corpora.

*   **Spanish-English (LinCE):** 0.9450 Macro F1 | 94.53% Token Accuracy
*   **Turkish-English (LinCE):** 0.8278 Macro F1 | 86.93% Token Accuracy

## Academic Web Interface (Workbench)

PolyBeta V5 comes with a robust Flask-based Academic Web Interface designed for real-time forensic trace analysis of code-switched text.

### Quick Start / Deployment

**Local Run:**
```bash
pip install -r requirements.txt
cd webapp
python app.py
```

**Hugging Face Spaces Deployment:**
This repository is pre-configured for Docker-based deployment on [Hugging Face Spaces](https://huggingface.co/spaces).
1. Create a Docker Space on Hugging Face.
2. Link this GitHub repository in the Space settings.
3. The Space will automatically build and launch using the provided `Dockerfile` and Gunicorn server.

## Academic Documentation

The complete theoretical foundation, formal taxonomy of failure modes (Candidate Discovery Failure, Lexical Ambiguity, Loanwords, Named Entities, and Boundary Errors), and experimental setup can be found in the `/thesis` directory.
