import pytest
import os
import pandas as pd
import json

def test_all_final_artifacts_exist():
    artifacts = [
        "results/benchmarks/benchmark_results_final.csv",
        "results/benchmarks/per_language_metrics.csv",
        "results/benchmarks/overall_metrics.json",
        "results/benchmarks/combined_token_classification_report.csv",
        "results/benchmarks/combined_token_confusion_matrix.csv",
        "results/benchmarks/benchmark_validation_report_final.md",
        "results/thesis/table_unit_tests.csv",
        "results/thesis/table_benchmark_results.csv",
        "results/thesis/table_per_language_results.csv",
        "results/thesis/table_overall_results.csv",
        "results/thesis/table_dataset_limitations.csv",
        "results/thesis/chart_dataset_accuracy_f1.csv",
        "results/thesis/chart_sequence_boundary_metrics.csv",
        "results/thesis/chart_per_language_f1.csv"
    ]
    for artifact in artifacts:
        assert os.path.exists(artifact), f"Missing artifact: {artifact}"

def test_every_artifact_uses_the_same_commit_hash():
    # Only verify across CSV and JSON that embed the commit hash
    df1 = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    df2 = pd.read_csv("results/benchmarks/per_language_metrics.csv")
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
        
    hash1 = set(df1["source_revision"])
    hash2 = set(df2["source_revision"])
    
    assert len(hash1) == 1
    assert len(hash2) == 1
    assert list(hash1)[0] == list(hash2)[0] == overall["source_revision"]

def test_timezone_aware_timestamps():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    for ts in df["execution_timestamp_utc"]:
        assert "+00:00" in ts or "Z" in ts

def test_aggregate_csv_contains_script_topology_and_split():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    assert "script_topology" in df.columns
    assert "split" in df.columns
    
def test_obsolete_topology_column_is_absent():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    assert "topology" not in df.columns

def test_split_is_test_for_current_rows():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    assert (df["split"] == "test").all()

def test_dataset_totals():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
        
    assert overall["total_sentences"] == 5877
    assert overall["total_gold_tokens"] == 135993
    assert overall["total_evaluated_tokens"] == 126224
    assert overall["total_ignored_tokens"] == 9769
    assert overall["total_correct_tokens"] == 113066

def test_evaluated_plus_ignored_equals_total_gold():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    assert (df["evaluated_tokens"] + df["ignored_tokens"] == df["total_gold_tokens"]).all()

def test_pooled_accuracy_equals_correct_divided_by_evaluated():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
        
    expected_acc = overall["total_correct_tokens"] / overall["total_evaluated_tokens"]
    assert overall["pooled_token_accuracy"] == pytest.approx(expected_acc)
    
def test_overall_boundary_metrics_reproduce():
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
        
    tp = overall["boundary_tp"]
    fp = overall["boundary_fp"]
    fn = overall["boundary_fn"]
    
    expected_p = tp / (tp + fp) if (tp + fp) > 0 else 0
    expected_r = tp / (tp + fn) if (tp + fn) > 0 else 0
    expected_f1 = 2 * expected_p * expected_r / (expected_p + expected_r) if (expected_p + expected_r) > 0 else 0
    
    assert overall["pooled_boundary_precision"] == pytest.approx(expected_p)
    assert overall["pooled_boundary_recall"] == pytest.approx(expected_r)
    assert overall["pooled_boundary_f1"] == pytest.approx(expected_f1)

def test_macro_f1_values():
    df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    
    ts_f1 = df[df["dataset"] == "tongueswitcher_de_en"]["macro_f1"].iloc[0]
    assert ts_f1 == pytest.approx(0.9103071537761438, abs=1e-12)
    
    tg_f1 = df[df["dataset"] == "turkish_german"]["macro_f1"].iloc[0]
    assert tg_f1 == pytest.approx(0.9259136609778953, abs=1e-12)
    
    with open("results/benchmarks/overall_metrics.json", "r") as f:
        overall = json.load(f)
    assert overall["dataset_macro_f1"] == pytest.approx(0.8765199136127393, abs=1e-12)
