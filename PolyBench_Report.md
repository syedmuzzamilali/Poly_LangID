# PolyBench Evaluation Report

**Dataset size:** 377

## Model Comparison Summary

| model    |   token_acc |   macro_f1 |   boundary_f1 |   latency_ms |   mem_mb |
|:---------|------------:|-----------:|--------------:|-------------:|---------:|
| polybeta |    0.869312 |   0.827828 |      0.384787 |      2.38395 |  245.703 |


## polybeta

### Metrics

|   token_acc |   macro_f1 |   weighted_f1 |   boundary_f1 |   span_exact |   span_overlap |   avg_latency_ms |   p95_latency_ms |   throughput_tps |   peak_mem_mb |   error_total |
|------------:|-----------:|--------------:|--------------:|-------------:|---------------:|-----------------:|-----------------:|-----------------:|--------------:|--------------:|
|    0.869312 |   0.827828 |      0.863986 |      0.384787 |   0.00607735 |              1 |          2.38395 |          3.62251 |           293.16 |       245.703 |          5500 |


### polybeta Per-language Classification Report

| label        |   precision |   recall |   f1-score |     support |
|:-------------|------------:|---------:|-----------:|------------:|
| en           |    0.8483   | 0.661455 |   0.743316 | 1471        |
| tr           |    0.875344 | 0.952601 |   0.91234  | 3671        |
| accuracy     |    0.869312 | 0.869312 |   0.869312 |    0.869312 |
| macro avg    |    0.861822 | 0.807028 |   0.827828 | 5142        |
| weighted avg |    0.867607 | 0.869312 |   0.863986 | 5142        |


### polybeta Confusion Matrix

| gold/pred   |   en |   tr |
|:------------|-----:|-----:|
| en          |  973 |  498 |
| tr          |  174 | 3497 |


### polybeta Error Taxonomy

| error_type     |   count |
|:---------------|--------:|
| missed_span    |    4716 |
| boundary_error |     681 |
| wrong_language |     103 |


### polybeta Top Confusions

| gold   | pred   |   count |
|:-------|:-------|--------:|
| en     | tr     |     498 |
| tr     | en     |     174 |


### polybeta Boundary Errors by Script

| script   |   boundary_pairs |   boundary_errors |   error_rate |
|:---------|-----------------:|------------------:|-------------:|
| LATIN    |             4765 |               825 |     0.173137 |

