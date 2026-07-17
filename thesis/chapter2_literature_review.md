# Chapter 2: Literature Review

## 2.1 Evolution of Language Identification Systems

Language Identification (LID) is one of the foundational classification problems in computational linguistics. Early approaches to LID relied on Markov models of character n-gram frequencies and rank-order statistics (Beesley, 1988; Cavnar & Trenkle, 1994). By comparing character n-gram profiles of target text against pre-compiled language profiles using out-of-place (OOV) distance metrics, statistical LID systems achieved high accuracy on long, monolingual documents.

With the proliferation of digital communication, research shifted toward linear classifiers over subword representations. Joulin et al. (2017) introduced FastText, demonstrating that linear classification over bag-of-words and subword n-gram features could achieve competitive accuracy with deep neural networks while maintaining low parameter footprints. FastText remains a standard baseline for document and sentence-level language identification across 176 languages (`lid.176.ftz`).

## 2.2 Token-Level Language Identification & Code-Switching

While sentence-level LID has reached over 99% accuracy on standardized monolingual corpora, token-level language identification in code-switched text remains an active research challenge. Code-switching involves the fluid alternation of grammatical paradigms within or across sentences (Poplack, 1980; Myers-Scotton, 1993).

To standardize evaluation across multilingual NLP systems, Aguilar et al. (2020) established the Linguistic Code-Switching Evaluation (LinCE) benchmark. LinCE provides token-level annotations for conversational code-switching pairs, including Spanish-English (`lince_spaeng`) and Turkish-English (`lince_turen`). Research on LinCE has revealed that token-level classifiers struggle with severe class imbalance, lexical borrowing, and homographs across languages sharing scripts.

## 2.3 Limitations of Existing Paradigms

Existing token-level LID systems generally fall into two architectural categories, both of which exhibit fundamental structural limitations:

### 2.3.1 Unconstrained Statistical Classifiers
When standard subword classifiers (e.g., FastText or statistical character n-gram probability tables) are applied independently to individual words across an open vocabulary $|\mathcal{L}|$, classification precision drops steeply. Because short tokens (e.g., *"no"*, *"a"*, *"en"*) share identical character n-grams across numerous Latin-script languages, unconstrained classifiers assign spurious labels (e.g., Portuguese, Italian, or Romanian) to tokens within a bilingual Spanish-English sentence.

### 2.3.2 Sequence Labeling & Spatial Smoothing
To address independent token errors, researchers have employed sequence labeling architectures such as Conditional Random Fields (CRFs), Hidden Markov Models (HMMs), and recurrent/transformer sequence models (King & Abney, 2013; Soto & Hirschberg, 2017). While sequence models capture transition probabilities between adjacent tokens, they introduce two critical vulnerabilities:
1. **Script & Boundary Blurring**: Spatial smoothing algorithms enforce continuity by encouraging adjacent tokens to share language labels. In code-switched discourse where switches occur abruptly across adjacent words, spatial smoothing frequently overrides correct minority-language predictions, erasing genuine code-switching boundaries.
2. **Fixed Transition Vocabularies**: Transition matrices trained on specific bilingual pairs fail to generalize when deployed on unconstrained multilingual inputs or novel language pairs.

## 2.4 Research Gap & Theoretical Motivation

A critical gap exists in current literature: **how to dynamically constrain the candidate search space of token-level language identification without imposing hardcoded language-pair assumptions or blurring intra-sentential code-switching boundaries.**

To bridge this gap, we introduce a **Context-First Hierarchical State-Transition Framework**. Rather than treating token identification as an isolated open-vocabulary classification task or applying post-hoc spatial smoothing over noisy predictions, our framework establishes a formal, state-transition discovery loop that identifies active candidate languages at the sentence level before restricting token classification and applying linguistically bounded phrase refinement.
