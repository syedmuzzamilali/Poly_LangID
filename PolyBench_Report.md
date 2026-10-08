# PolyBench Evaluation Report

**Dataset size:** 50

## Model Comparison Summary

| model   |   token_acc |   macro_f1 |   boundary_f1 |   exact_match |   partial_match |   latency_ms |   mem_mb |
|:--------|------------:|-----------:|--------------:|--------------:|----------------:|-------------:|---------:|
| polylid |    0.878735 |   0.843495 |       0.66436 |          0.32 |            0.96 |      194.327 |  2716.64 |


## polylid

### Metrics

|   token_acc |   macro_f1 |   weighted_f1 |   boundary_f1 |   exact_match |   partial_match |   span_exact |   span_overlap |   avg_latency_ms |   p95_latency_ms |   throughput_tps |   peak_mem_mb |   error_total |
|------------:|-----------:|--------------:|--------------:|--------------:|----------------:|-------------:|---------------:|-----------------:|-----------------:|-----------------:|--------------:|--------------:|
|    0.878735 |   0.843495 |      0.873905 |       0.66436 |          0.32 |            0.96 |    0.0870307 |              1 |          194.327 |          194.327 |          5.10676 |       2716.64 |           560 |


### polylid Per-language Classification Report

| label        |   precision |   recall |   f1-score |    support |
|:-------------|------------:|---------:|-----------:|-----------:|
| en           |    0.877863 | 0.684524 |   0.769231 | 168        |
| tr           |    0.878995 | 0.9601   |   0.917759 | 401        |
| accuracy     |    0.878735 | 0.878735 |   0.878735 |   0.878735 |
| macro avg    |    0.878429 | 0.822312 |   0.843495 | 569        |
| weighted avg |    0.878661 | 0.878735 |   0.873905 | 569        |


### polylid Confusion Matrix

| gold/pred   |   en |   tr |
|:------------|-----:|-----:|
| en          |  115 |   53 |
| tr          |   16 |  385 |


### polylid Error Taxonomy

| error_type     |   count |
|:---------------|--------:|
| missed_span    |     414 |
| boundary_error |     121 |
| wrong_language |      13 |
| extra_span     |      12 |


### polylid Top Confusions

| gold   | pred   |   count |
|:-------|:-------|--------:|
| en     | tr     |      53 |
| tr     | en     |      16 |


### polylid Boundary Errors by Script

| script   |   boundary_pairs |   boundary_errors |   error_rate |
|:---------|-----------------:|------------------:|-------------:|
| LATIN    |              519 |                97 |     0.186898 |

