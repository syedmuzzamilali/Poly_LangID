# Chapter 7: Conclusion, References & Appendix

## 7.1 Summary of Contributions

In this dissertation, we formulated, implemented, and empirically validated a **Context-First Hierarchical State-Transition Framework** for token-level language identification in multilingual and code-switched text.

The core scientific and architectural contributions of this research are summarized below:
1. **Algorithmic State-Transition Candidate Discovery**: We formulated global sentence language discovery as an iterative masking algorithm over state $(S_t, D_t)$, defined by $f: S_t \to C_t$, state update $D_{t+1} = D_t \cup C_t$, and masking operator $S_{t+1} = M(S_t, C_t)$. The process converges deterministically when $S_t = \varnothing$ or $C_t = \varnothing$, requiring fewer than three iterations on average (< 2.71 iterations).
2. **Search Space Reduction ($R$)**: We established that restricting the candidate search space from $|\mathcal{L}| = 26$ supported languages to $D_{\text{final}}$ achieves a **8.6× reduction** on Spanish-English code-switching and a **7.3× reduction** on Turkish-English code-switching while maintaining **91.9%–96.1% recall** of active gold languages.
3. **Script-Bounded Local Phrase Refinement**: We designed a selective local phrase context expansion operator bounded by script-transition points ($\sigma(w_j) \neq \sigma(w_i)$), resolving ambiguous tokens via evidence arbitration without blurring genuine code-switching boundaries.
4. **State-of-the-Art Empirical Benchmarking**: Under the standardized PolyBench protocol across 100% of records, the proposed framework achieved **0.9450 Macro F1** (94.53% Token Accuracy) on Spanish-English LinCE code-switching, **0.8278 Macro F1** (86.93% Token Accuracy) on Turkish-English LinCE code-switching, and **0.9461 Macro F1** (94.25% Token Accuracy, **0.9195 Boundary F1**) on the full 26-language `multilingual_codeswitched_10k` synthetic benchmark.
5. **Pipeline-Ordered Error Taxonomy**: We categorized residual token errors into a five-stage structural taxonomy—Candidate Discovery Failure, Lexical Ambiguity, Lexical Borrowing/Loanwords, Named Entities, and Boundary Errors.

## 7.2 Limitations & Future Directions

### 7.2.1 Primary Architectural Limitation
The framework assumes Level 1 Candidate Discovery has sufficiently high recall. Languages omitted during Level 1 cannot be recovered by downstream Level 2 token classifiers because token classification is strictly constrained to $D_{\text{final}}$.

### 7.2.2 Multilingual Candidate Competition
While Candidate Discovery achieves high recall on bilingual code-switching (91.9%–96.1%), performance decreases on highly multilingual trilingual discourse (66.67% recall on Hokaglish) due to probability competition across candidate languages during iterative discovery.

### 7.2.3 Future Work
Future research directions include:
- Incorporating named entity recognition (NER) masks during Level 1 discovery to prevent proper nouns from skewing language probabilities.
- Investigating subword etymological embeddings to better distinguish historical loanwords from active code-switching.

---

## References

1. Aguilar, G., Kar, S., & Solorio, T. (2020). LinCE: A Centralized Benchmark for Linguistic Code-switching Evaluation. *Proceedings of the 12th Language Resources and Evaluation Conference (LREC)*, 1803–1813.
2. Beesley, K. R. (1988). Language Identifier: A Computer Program for Automatic Natural-Language Identification of On-Line Text. *Proceedings of the 29th Annual Conference of the American Translators Association*, 47–54.
3. Cavnar, W. B., & Trenkle, J. M. (1994). N-Gram-Based Text Categorization. *Proceedings of SDAIR-94, 3rd Annual Symposium on Document Analysis and Information Retrieval*, 161–175.
4. Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2017). Bag of Tricks for Efficient Text Classification. *Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics (EACL)*, 427–431.
5. King, B., & Abney, S. (2013). Labeling the Languages of Words in Mixed-Language Documents using Weakly Supervised Methods. *Proceedings of NAACL-HLT*, 1110–1119.
6. Myers-Scotton, C. (1993). *Duelling Languages: Grammatical Structure in Codeswitching*. Oxford University Press.
7. Poplack, S. (1980). Sometimes I’ll start a sentence in Spanish Y TERMINO EN ESPAÑOL: toward a typology of code-switching. *Linguistics*, 18(7-8), 581–618.
8. Soto, V., & Hirschberg, J. (2017). Crowdsourcing Universal Part-Of-Speech Tags for Code-Switching. *Proceedings of Interspeech*, 3241–3245.

---

## Appendix A: Illustrative Verification Examples

**Table A.1: Representative Verification Examples of Level 1 State-Transition Discovery**
| True Languages | Sentence Text | Discovered Languages ($D_{\text{final}}$) | Precision | Recall | F1 |
|---|---|---|---|---|---|
| **en + hi** | *"I like बिरयानी today"* | `en, hi` | 100.0% | 100.0% | 100.0% |
| **en + es** | *"gracias amigo see you soon"* | `en, es` | 100.0% | 100.0% | 100.0% |
| **en + hi + es** | *"I like बिरयानी today but gracias amigo"* | `en, es, hi` | 100.0% | 100.0% | 100.0% |
| **en + hi + ta** | *"I love बिरयानी and வணக்கம்"* | `en, hi, ta` | 100.0% | 100.0% | 100.0% |
| **en + es + fr** | *"hello amigo bonjour mon ami"* | `en, es, fr` | 100.0% | 100.0% | 100.0% |
