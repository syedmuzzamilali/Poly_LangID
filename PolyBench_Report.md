# PolyBench Evaluation Report

**Dataset size:** 2943

## Model Comparison Summary

| model    |   token_acc |   macro_f1 |   boundary_f1 |   latency_ms |   mem_mb |
|:---------|------------:|-----------:|--------------:|-------------:|---------:|
| polybeta |    0.945503 |   0.945165 |      0.422456 |      1.18972 |  275.309 |


## polybeta

### Metrics

|   token_acc |   macro_f1 |   weighted_f1 |   boundary_f1 |   span_exact |   span_overlap |   avg_latency_ms |   p95_latency_ms |   throughput_tps |   peak_mem_mb |   error_total |
|------------:|-----------:|--------------:|--------------:|-------------:|---------------:|-----------------:|-----------------:|-----------------:|--------------:|--------------:|
|    0.945503 |   0.945165 |      0.945567 |      0.422456 |    0.0101676 |              1 |          1.18972 |          2.04369 |          529.816 |       275.309 |         35386 |


### polybeta Per-language Classification Report

| label        |   precision |   recall |   f1-score |      support |
|:-------------|------------:|---------:|-----------:|-------------:|
| en           |    0.930462 | 0.95127  |   0.940751 | 11492        |
| es           |    0.958629 | 0.940699 |   0.949579 | 13794        |
| und          |    0        | 0        |   0        |     0        |
| accuracy     |    0.945503 | 0.945503 |   0.945503 |     0.945503 |
| macro avg    |    0.629697 | 0.630656 |   0.63011  | 25286        |
| weighted avg |    0.945828 | 0.945503 |   0.945567 | 25286        |


### polybeta Confusion Matrix

| gold/pred   |    en |    es |   und |
|:------------|------:|------:|------:|
| en          | 10932 |   560 |     0 |
| es          |   817 | 12976 |     1 |
| und         |     0 |     0 |     0 |


### polybeta Error Taxonomy

| error_type     |   count |
|:---------------|--------:|
| missed_span    |   29555 |
| boundary_error |    3934 |
| wrong_language |    1751 |
| extra_span     |     146 |


### polybeta Top Confusions

| gold   | pred   |   count |
|:-------|:-------|--------:|
| es     | en     |     817 |
| en     | es     |     560 |
| es     | und    |       1 |


### polybeta Boundary Errors by Script

| script   |   boundary_pairs |   boundary_errors |   error_rate |
|:---------|-----------------:|------------------:|-------------:|
| LATIN    |            22476 |              1430 |    0.0636234 |

