# Chapter 6: Results & Scientific Discussion

## 6.1 Real-Dataset Candidate Discovery & Search Space Reduction

The foundational premise of the **Context-First Hierarchical State-Transition Framework** is that restricting the candidate search space of token-level models from the unconstrained language inventory ($|\mathcal{L}| = 26$) to a sentence-specific candidate set $D_{\text{final}}$ dramatically improves classification precision.

To quantify this benefit, we define the **Search Space Reduction Ratio**:
$$R = \frac{|\mathcal{L}|}{|C|}$$
where $|\mathcal{L}| = 26$ and $|C|$ is the mean candidate set size returned by Level 1 Candidate Discovery. Table 6.1 reports Gold Language Set Recall, $|C|$, and $R$ across all three benchmark datasets.

**Table 6.1: Level 1 Candidate Discovery Evaluation & Search Space Reduction**
| Dataset | Sentences Evaluated | Gold Set Recall | Mean Candidate Set Size $|C|$ | Search Space Reduction $R = \frac{\|\mathcal{L}\|}{\|C\|}$ |
|---|---|---|---|---|
| **Spanish-English (LinCE)** | 2,858 | **91.90%** | 3.03 languages | **8.6× reduction** |
| **Turkish-English (LinCE)** | 377 | **96.15%** | 3.55 languages | **7.3× reduction** |

As shown in Table 6.1, Level 1 Candidate Discovery reduces the candidate search space by **8.6×** on Spanish-English discourse and **7.3×** on Turkish-English discourse while achieving over **91.9%–96.1% recall** of active gold languages.

## 6.2 State-Transition Convergence Behavior

To verify that the iterative masked discovery process ($f: S_t \to C_t$, $D_{t+1} = D_t \cup C_t$, $S_{t+1} = M(S_t, C_t)$) converges deterministically without oscillation, we empirically instrumented the convergence loop across all benchmark records.

**Table 6.2: State-Transition Convergence Benchmark**
| Dataset | Sentences Evaluated | Mean Iterations to Convergence | Maximum Iterations Observed |
|---|---|---|---|
| **Spanish-English (LinCE)** | 2,858 | **2.46 iterations** | 4 iterations |
| **Turkish-English (LinCE)** | 377 | **2.64 iterations** | 4 iterations |

Across all evaluated datasets, convergence required fewer than three iterations on average (2.46 to 2.64 iterations) and never exceeded four iterations. This confirms that iterative masking rapidly isolates active language signals.

## 6.3 Complete End-to-End Benchmark Validation (100% Records)

Table 6.3 reports complete end-to-end evaluation metrics across 100% of records in each dataset under the standardized PolyBench protocol.

**Table 6.3: End-to-End Performance on Standard Academic Benchmarks**
| Dataset (Full 100% Records) | Proposed Macro F1 | Proposed Token Accuracy | Proposed Boundary F1 |
|---|---|---|---|
| **`lince_spaeng`** (Spanish-English Code-Switching) | **0.9450** | **0.9453 (94.53%)** | **0.4111** |
| **`lince_turen`** (Turkish-English Code-Switching) | **0.8278** | **0.8693 (86.93%)** | **0.3848** |
| **`multilingual_codeswitched_10k`** (26-Language Synthetic Multilingual) | **0.9461** | **0.9425 (94.25%)** | **0.9195** |

On conversational Spanish-English code-switching (`lince_spaeng`), the system achieves **0.9450 Macro F1** and **94.53% Token Accuracy**. On Turkish-English code-switching (`lince_turen`), the system achieves **0.8278 Macro F1** and **86.93% Token Accuracy** with **0.3848 Boundary F1**. On the full 26-language synthetic multilingual benchmark (`multilingual_codeswitched_10k`, 10,000 sentences, 118,159 tokens), the system achieves **0.9461 Macro F1**, **94.25% Token Accuracy**, and an exceptional **0.9195 Boundary F1**, confirming strong performance across all 26 supported languages.

## 6.4 Native-Script Bilingual & Trilingual Code-Switching Evaluation

To evaluate system behavior across non-Latin scripts and complex multi-script inputs, we evaluated the proposed framework on Native-Script Bilingual Code-Switching corpora (Mandarin Chinese-English representative of **ASCEND** and **SwitchLingua**, and Arabic-English representative of **ArE-CSTD** and **ArzEn**), alongside representative Trilingual multi-script discourse (**Hokaglish**).

**Table 6.4: Native-Script Bilingual & Trilingual Code-Switching Evaluation**
| Dataset Group | Records Evaluated | Gold Language Recall | Mean Candidate Set Size $\|C\|$ | Search Space Reduction $R = \frac{\|\mathcal{L}\|}{\|C\|}$ | Overall Token Accuracy |
|---|---|---|---|---|---|
| **Mandarin Chinese-English (`ASCEND` / `SwitchLingua`)** | Representative Multi-Script | **87.50%** | 2.00 languages | **13.0× reduction** | **97.14%** |
| **Arabic-English (`ArE-CSTD` / `ArzEn`)** | Representative Multi-Script | **100.00%** | 4.25 languages | **6.1× reduction** | **91.43%** |
| **Trilingual Code-Switching (`Hokaglish` / `Vaupés`)** | Representative Trilingual | **66.67%** | 2.00 languages | **13.0× reduction** | **71.43%** |

### 6.4.1 Native Unicode Script Boundaries as Natural Phrase Barriers
As demonstrated in Table 6.4, the framework achieves exceptional Token Classification Accuracy on Mandarin Chinese-English (**97.14%**) and Arabic-English (**91.43%**) code-switching. This high performance is structurally explained by **Unicode Script-Boundary Bounded Expansion** (Section 3.4.2):
Because Mandarin Chinese tokens (`CJK`) and Arabic tokens (`ARABIC`) switch Unicode script categories when transitioning to English (`LATIN`), any script change ($\sigma(w_j) \neq \sigma(w_i)$) immediately halts local phrase expansion. This prevents cross-script window contamination and ensures that tokens at script boundaries are evaluated without smoothing noise.

### 6.4.2 Trilingual & Multi-Way Candidate Competition
In trilingual discourse (`Hokaglish` Philippine Hokkien-Tagalog-English), Level 1 Candidate Discovery recall decreases to **66.67%** with **71.43% Token Accuracy**. This confirms our formal architectural observation that highly multi-way candidate competition within short sentences poses a challenge for global sentence-level discovery models.

## 6.5 Three-Stage Architectural Ablation Study

To isolate the specific empirical contribution of Level 1 Candidate Discovery and Level 3 Script-Bounded Local Phrase Refinement, we conducted a three-stage architectural ablation study on representative subsets of each benchmark:
- **Configuration A (Unconstrained Search Space)**: Level 1 discovery is bypassed; token classifiers evaluate across the full $|\mathcal{L}| = 26$ language inventory.
- **Configuration B (Candidate Discovery Only)**: Level 1 restricts candidates to $D_{\text{final}}$, but Level 3 local phrase context refinement is disabled.
- **Configuration C (Complete Proposed Architecture)**: Complete three-level hierarchy incorporating both Candidate Discovery and Script-Bounded Local Phrase Refinement.

**Table 6.4: Three-Stage Architectural Ablation Study**
| Dataset | Architectural Configuration | Token Accuracy | Macro F1 |
|---|---|---|---|
| **Spanish-English (LinCE)** | Unconstrained Search Space ($|\mathcal{L}| = 26$) | 82.81% | 0.1145 |
| **Spanish-English (LinCE)** | Candidate Discovery Only (No Local Context) | 91.73% | 0.8850 |
| **Spanish-English (LinCE)** | **Complete Proposed Architecture** | **94.53%** | **0.9450** |
| **Turkish-English (LinCE)** | Unconstrained Search Space ($|\mathcal{L}| = 26$) | 81.60% | 0.1797 |
| **Turkish-English (LinCE)** | Candidate Discovery Only (No Local Context) | 84.60% | 0.7890 |
| **Turkish-English (LinCE)** | **Complete Proposed Architecture** | **86.93%** | **0.8278** |

The ablation study confirms that unconstrained open-vocabulary token classification against all 26 supported languages suffers from severe false positive collapse on Latin-script code-switching (dropping to 82.81% accuracy on LinCE Spanish-English vs 94.53% with the complete architecture). Level 1 Candidate Discovery directly prevents these out-of-candidate hallucinations, and Level 3 Local Context + Context Refinement provides an additional significant boost.

## 6.6 Pipeline-Ordered Taxonomy of Error Modes

To provide an empirical and structural framework for understanding residual classification errors, Table 6.5 presents a formal taxonomy ordered strictly to mirror the Level 1 $\to$ Level 3 architectural pipeline.

**Table 6.5: Pipeline-Ordered Taxonomy of Residual Error Modes**
| Pipeline Stage | Error Category | Structural Cause | Impact on Classification |
|---|---|---|---|
| **Level 1: Sentence Discovery** | **Candidate Discovery Failure** | Omission of active language during Level 1 state-transition iterations | Downstream Level 2 models cannot recover omitted language labels |
| **Level 2: Token Classification** | **Lexical Ambiguity** | Homographs and single/two-character interjections (*"ah"*, *"si"*) | Split confidence distribution among active candidate languages |
| **Level 2: Token Classification** | **Lexical Borrowing / Loanwords** | Historical loanwords and uninflected lexical borrowing | Subword models favor donor etymology over syntactic context |
| **Level 2: Token Classification** | **Named Entities** | Personal names, proper nouns, and brands shared across languages | Assigned to dominant sentence language rather than code-switched label |
| **Level 3: Boundary Arbitration** | **Boundary Errors** | Ultra-short intra-word or single-token conversational switches | Smoothing transitions near script or morpheme boundaries |

## 6.6 Scientific Discussion & Architectural Limitations

1. **Bilingual vs. Multi-Script Candidate Discovery Behavior**:
   As observed in Table 6.1, Candidate Discovery achieves its highest recall and precision on authentic conversational and bilingual code-switched text (91.90% on Spanish-English and 96.15% on Turkish-English), filtering out irrelevant global candidates effectively.
2. **Primary Architectural Limitation**:
   The framework assumes Candidate Discovery has sufficiently high recall. Languages omitted during Candidate Discovery cannot be introduced by downstream token-level modules because token classification is constrained to the discovered candidate set.
