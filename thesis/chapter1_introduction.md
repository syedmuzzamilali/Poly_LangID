# Chapter 1: Introduction

## 1.1 Background & Motivation

Natural language communication on digital platforms, particularly across social media, instant messaging, and conversational interfaces, is increasingly characterized by multilingualism and **code-switching**—the alternating use of two or more languages or dialects within a single conversational discourse or sentence. In linguistically diverse societies, multilingual users routinely blend languages across grammatical and structural boundaries.

Accurately identifying the language of individual tokens in code-switched text is a foundational prerequisite for downstream natural language processing (NLP) pipelines, including machine translation, speech recognition, syntactic parsing, semantic role labeling, and sentiment analysis. When an NLP pipeline misidentifies the language of a token, downstream processors apply incorrect grammatical paradigms or vocabulary lookups, leading to compounding errors across multi-step systems.

## 1.2 The Problem of Unconstrained Token-Level Language Identification

Conventional approaches to language identification (LID) operate either at the document/sentence level or at the isolated token level:

1. **Sentence-Level LID Models**: Global sentence classifiers exhibit high statistical reliability because they aggregate extensive n-gram and subword evidence across the entire input sequence. However, by assigning a monolithic label to an entire sequence, sentence-level classifiers fundamentally fail on code-switched sentences, obscuring fine-grained intra-sentential transitions.
2. **Unconstrained Token-Level Classifiers**: To capture intra-sentential switches, token-level classifiers evaluate each word individually across an open vocabulary of dozens or hundreds of supported languages ($|\mathcal{L}|$). However, evaluating short tokens against an unconstrained search space induces severe precision degradation due to three structural ambiguities:
   - **Lexical Ambiguity & Interjections**: Short tokens (e.g., *"no"*, *"in"*, *"ah"*, *"si"*) are homographs shared across numerous Latin-script languages. An unconstrained classifier frequently assigns such tokens to unrelated background languages (e.g., Italian or Portuguese within a Spanish-English sentence).
   - **Proper Nouns & Entities**: Personal names, geographic locations, and brand names lack distinctive language-specific inflections, leading statistical models to hallucinate arbitrary languages.
   - **Lexical Borrowing & Loanwords**: Historical loanwords carry etymological n-grams from their donor language despite functioning syntactically within a different host language.

Consequently, open-vocabulary token-level classification suffers from severe candidate over-prediction and low precision.

## 1.3 Proposed Approach: Context-First Hierarchical State-Transition Framework

To resolve the fundamental tension between global sentence context and token-level granularity without relying on ad-hoc heuristics, we propose a novel **Context-First Hierarchical State-Transition Framework** for token-level language identification.

The central thesis of this research is that **global syntactic and document context must constrain the candidate search space of token-level classification**. Rather than allowing token models to search across an unconstrained language inventory $|\mathcal{L}|$, the proposed architecture enforces a strict three-level contextual hierarchy:

```
                  Input Sentence S
                         │
                         ▼
        Level 1: Global Candidate Discovery
       (Iterative Masked State Transition)
                         │
                         ▼
             Restricted Candidate Set D
                         │
                         ▼
      Level 2: Restricted Token Classification
              (FastText + Lingua Experts)
                         │
                         ▼
       Level 3: Boundary & Local Context Analysis
           (Script-Bounded Phrase Expansion)
                         │
                         ▼
             Final Token-Level Predictions
```

1. **Level 1 (Global Candidate Discovery via State-Transition Iteration)**: An algorithmic iterative masked discovery process operates over sentence state $(S_t, D_t)$ to discover the subset of active languages $D_{\text{final}} \subseteq \mathcal{L}$ present in the sentence. Newly discovered languages are iteratively masked from the remaining text until state convergence ($S_t = \varnothing$ or $C_t = \varnothing$).
2. **Level 2 (Restricted Token Classification)**: Token-level subword and character n-gram models evaluate each word strictly within the restricted candidate set $D_{\text{final}}$, reducing search space dimensionality and eliminating out-of-candidate false positives.
3. **Level 3 (Boundary Analysis & Script-Bounded Local Context Refinement)**: For tokens exhibiting low decision margins or boundary ambiguity, the framework performs selective local phrase context expansion—extending left and right up to script boundaries—before applying an evidence-based arbitration protocol.

## 1.4 Research Objectives

The primary research objectives of this dissertation are:
1. **Mathematical Formalization**: Formulate candidate language discovery as a deterministic, state-transition iterative masking algorithm over $(S_t, D_t)$ with rigorous stopping criteria.
2. **Search Space Optimization**: Quantify the reduction in candidate search space $R = \frac{|\mathcal{L}|}{|C|}$ achieved by global candidate discovery and measure its impact on token-level classification accuracy.
3. **Boundary-Aware Contextual Arbitration**: Design a selective local context refinement mechanism bounded by script transitions to resolve ambiguous token classifications without distorting true code-switching boundaries.
4. **Empirical Benchmarking & Taxonomy**: Systematically evaluate the proposed framework against standard multilingual and code-switching benchmarks and establish a formal taxonomy of token-level LID failure modes.

## 1.5 Dissertation Organization

The remainder of this dissertation is organized as follows:
- **Chapter 2 (Literature Review)** reviews historical and contemporary methodologies in language identification, subword modeling, code-switching analysis, and contextual disambiguation.
- **Chapter 3 (Proposed Framework)** details the mathematical specification, state-transition discovery loop, restricted token classification, and boundary-aware arbitration architecture.
- **Chapter 4 (Implementation)** presents the modular object-oriented software design implementing the proposed framework.
- **Chapter 5 (Experimental Setup)** describes the benchmark datasets, PolyBench evaluation protocol, and quantitative evaluation metrics.
- **Chapter 6 (Results & Discussion)** presents empirical evaluation results, search space reduction ratios, convergence behavior, ablation studies, and a formal error taxonomy.
- **Chapter 7 (Conclusion & Future Work)** summarizes key contributions and outlines directions for future research.
