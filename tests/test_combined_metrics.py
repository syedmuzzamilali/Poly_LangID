import pytest
import pandas as pd
import json

def test_combined_lengths():
    cm_df = pd.read_csv("results/benchmarks/combined_token_confusion_matrix_union.csv", index_col=0)
    assert len(cm_df.index) == 11
    assert len(cm_df.columns) == 11

def test_union_matrix_contains_all_tokens():
    cm_df = pd.read_csv("results/benchmarks/combined_token_confusion_matrix_union.csv", index_col=0)
    assert int(cm_df.values.sum()) == 126224

def test_union_matrix_correct_diagonal():
    cm_df = pd.read_csv("results/benchmarks/combined_token_confusion_matrix_union.csv", index_col=0)
    import numpy as np
    assert int(np.diag(cm_df.values).sum()) == 113066

def test_predicted_only_counts():
    po_df = pd.read_csv("results/benchmarks/predicted_only_labels.csv")
    po_dict = dict(zip(po_df["label"], po_df["prediction_count"]))
    assert po_dict == {
        "el": 16,
        "ja": 4,
        "kn": 4,
        "th": 4,
    }

def test_micro_metrics_equal_accuracy():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
    
    acc = overall["pooled_token_accuracy"]
    assert overall["micro_precision"] == pytest.approx(acc, abs=1e-12)
    assert overall["micro_recall"] == pytest.approx(acc, abs=1e-12)
    assert overall["micro_f1"] == pytest.approx(acc, abs=1e-12)

def test_expected_label_macro_f1():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
    assert overall["combined_expected_label_macro_f1"] == pytest.approx(0.8910063090773125, abs=1e-12)

def test_union_label_macro_f1():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
    assert overall["combined_union_label_macro_f1"] == pytest.approx(0.5670040148673807, abs=1e-12)

def test_combined_weighted_f1():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
    assert overall["combined_token_weighted_f1"] == pytest.approx(0.8922182997775683, abs=1e-12)
