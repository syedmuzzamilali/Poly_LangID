import pytest
import os
import pandas as pd
from polylid import LANG_NAME_TO_CODE

def test_benchmark_integrity():
    if os.path.exists("results/benchmarks/benchmark_results_final.csv"):
        df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
        
        # correct-token count never exceeds evaluated-token count
        assert (df["correct_tokens"] <= df["evaluated_tokens"]).all()
        
        # evaluated tokens plus ignored tokens equal total gold tokens
        assert (df["evaluated_tokens"] + df["ignored_tokens"] == df["total_gold_tokens"]).all()
        
        # Boundary TP, FP, FN are non-negative integers
        for col in ["boundary_tp", "boundary_fp", "boundary_fn"]:
            assert (df[col] >= 0).all()
            assert (df[col] % 1 == 0).all()  # is integer
        
        # All reported scalar metrics lie in the interval [0, 1]
        for col in ["token_accuracy", "macro_f1", "weighted_f1", "exact_match", "partial_match", 
                    "boundary_precision", "boundary_recall", "boundary_f1"]:
            if col in df.columns:
                assert (df[col] >= 0.0).all()
                assert (df[col] <= 1.0).all()

def test_language_inventory():
    assert len(set(LANG_NAME_TO_CODE.values())) == 66
    
def test_per_language_supports_sum_to_evaluated_token_count():
    if os.path.exists("results/benchmarks/per_language_metrics.csv") and os.path.exists("results/benchmarks/benchmark_results_final.csv"):
        df_lang = pd.read_csv("results/benchmarks/per_language_metrics.csv")
        df_agg = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
        
        for dataset in df_agg["dataset"].unique():
            sum_support = df_lang[df_lang["dataset"] == dataset]["support"].sum()
            evaluated = df_agg[df_agg["dataset"] == dataset]["evaluated_tokens"].iloc[0]
            assert sum_support == evaluated
