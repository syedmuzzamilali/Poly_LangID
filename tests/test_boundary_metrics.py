import pytest
from evaluation.metrics import boundary_metrics

def test_empty_boundary_sets_do_not_create_misleading_scores():
    # If both sets are empty for a sentence, exclude that sentence from precision and recall
    # while retaining it for token and sequence metrics
    gold = [["en", "en"]]
    pred = [["en", "en"]]
    metrics = boundary_metrics(gold, pred, ignored_labels={"un", "und"})
    assert metrics["total_gold_boundaries"] == 0
    assert metrics["total_pred_boundaries"] == 0
    # Because there are no boundaries at all across the dataset, precision/recall should be 0.0 per standard definition
    assert metrics["boundary_precision"] == 0.0
    assert metrics["boundary_recall"] == 0.0
    assert metrics["boundary_f1"] == 0.0

def test_pooled_boundary_counts():
    gold = [
        ["en", "en"],           # 0
        ["en", "de", "en"],     # 2
    ]
    pred = [
        ["en", "de"],           # 1
        ["en", "en", "en"],     # 0
    ]
    metrics = boundary_metrics(gold, pred, ignored_labels={"un", "und"})
    assert metrics["total_gold_boundaries"] == 2
    assert metrics["total_pred_boundaries"] == 1
    assert metrics["true_positives"] == 0
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 2
