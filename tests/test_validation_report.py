import pytest
import os

def test_validation_report_content():
    with open("results/benchmarks/benchmark_validation_report_final.md", "r") as f:
        content = f.read()
        
    assert "69.80%" not in content, "Report contains obsolete 69.80%"
    assert "Arabic-English having 1,000 evaluated sentences" not in content, "Report contains obsolete Arabic sentence count"
    assert "26.01%" not in content, "Report contains obsolete TongueSwitcher macro F1"
    assert "61.73%" not in content, "Report contains obsolete Turkish-German macro F1"
    
    assert "Partial Match is the mean sentence-level token agreement" in content
    assert "Partial Match measures boundary alignment" not in content
    assert "FastText strictly equates Latin script with English" not in content
