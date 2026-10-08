import pytest
import os
import pandas as pd
from datetime import datetime

def test_benchmark_columns_do_not_contain_per_language_metrics():
    if os.path.exists("results/benchmarks/benchmark_results_final.csv"):
        df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
        
        # Ensure we don't have columns like precision_en
        for col in df.columns:
            assert not col.startswith("precision_")
            assert not col.startswith("recall_")
            assert not col.startswith("f1_")
            assert not col.startswith("support_")

def test_per_language_metrics_long_format():
    if os.path.exists("results/benchmarks/per_language_metrics.csv"):
        df = pd.read_csv("results/benchmarks/per_language_metrics.csv")
        
        expected_cols = ["dataset", "language", "precision", "recall", "f1", "support", "source_revision", "execution_timestamp_utc"]
        for col in expected_cols:
            assert col in df.columns
            
        assert len(df.columns) == len(expected_cols)

def test_utc_timestamp_has_offset():
    if os.path.exists("results/benchmarks/benchmark_results_final.csv"):
        df = pd.read_csv("results/benchmarks/benchmark_results_final.csv")
        timestamp_str = df["execution_timestamp_utc"].iloc[0]
        
        dt = datetime.fromisoformat(timestamp_str)
        assert dt.tzinfo is not None, "Timestamp must have a UTC offset"
        assert dt.tzinfo.utcoffset(dt).total_seconds() == 0, "Timestamp must be strictly UTC (+00:00)"
