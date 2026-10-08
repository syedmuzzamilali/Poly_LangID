import pytest
import os
import pandas as pd
import json

def test_thesis_ready_percentages_are_rounded():
    df = pd.read_csv("results/thesis/table_benchmark_results.csv")
    for col in ["Token accuracy (%)", "Macro F1 (%)", "Exact Match (%)", "Partial Match (%)", "Boundary F1 (%)"]:
        for val in df[col]:
            # Should have exactly two decimal places
            assert str(val).split(".")[1] == "00" or len(str(val).split(".")[1]) == 2

def test_thesis_ready_counts_are_integers():
    df = pd.read_csv("results/thesis/table_benchmark_results.csv")
    for val in df["Sentences"]:
        assert "." not in str(val)
        
    for val in df["Evaluated tokens"]:
        assert "." not in str(val)

def test_per_language_supports_match_aggregate_evaluated_tokens():
    df_agg = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
    df_pl = pd.read_csv("results/benchmarks/per_language_metrics.csv")
    
    for dataset in df_agg["dataset"].unique():
        agg_val = df_agg[df_agg["dataset"] == dataset]["evaluated_tokens"].iloc[0]
        pl_val = df_pl[df_pl["dataset"] == dataset]["support"].sum()
        assert agg_val == pl_val

def test_combined_token_metric_support():
    df = pd.read_csv("results/benchmarks/combined_token_classification_report.csv", index_col=0)
    
    # "support" in classification report
    # The last row is usually 'macro avg', 'weighted avg', etc. 
    # But for individual classes, their sum should be 126224.
    # Actually, we can just get the 'support' column and sum the individual labels (which are not strings like 'accuracy', 'macro avg', 'weighted avg').
    individual_labels = [idx for idx in df.index if idx not in ["accuracy", "macro avg", "weighted avg"]]
    total_support = df.loc[individual_labels, "support"].sum()
    assert total_support == 126224

def test_no_zero_support_label_appears_in_per_language_output():
    df = pd.read_csv("results/benchmarks/per_language_metrics.csv")
    assert (df["support"] > 0).all()
