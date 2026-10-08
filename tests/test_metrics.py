import pytest
from evaluation.metrics import (
    token_accuracy,
    strict_exact_match,
    sentence_partial_match,
    switch_boundaries,
    boundary_metrics,
    per_language_metrics
)

def test_perfect_predictions():
    gold = ["en", "en", "fr"]
    pred = ["en", "en", "fr"]
    assert token_accuracy(gold, pred) == 1.0
    
    gold_seq = [["en", "en"], ["fr", "fr"]]
    pred_seq = [["en", "en"], ["fr", "fr"]]
    assert strict_exact_match(gold_seq, pred_seq) == 1.0
    assert sentence_partial_match(gold_seq, pred_seq) == 1.0
    
    bm = boundary_metrics([gold], [pred])
    assert bm["boundary_precision"] == 1.0
    assert bm["boundary_recall"] == 1.0
    assert bm["boundary_f1"] == 1.0

def test_all_wrong_predictions():
    gold = ["en", "en"]
    pred = ["fr", "fr"]
    assert token_accuracy(gold, pred) == 0.0
    
    gold_seq = [["en", "en"]]
    pred_seq = [["fr", "fr"]]
    assert strict_exact_match(gold_seq, pred_seq) == 0.0
    assert sentence_partial_match(gold_seq, pred_seq) == 0.0

def test_one_partially_correct_sentence():
    gold_seq = [["en", "en", "fr", "fr"]]
    pred_seq = [["en", "en", "en", "en"]]
    assert strict_exact_match(gold_seq, pred_seq) == 0.0
    assert sentence_partial_match(gold_seq, pred_seq) == 0.5

def test_one_exact_sentence_one_incorrect_sentence():
    gold_seq = [["en", "en"], ["fr", "fr"]]
    pred_seq = [["en", "en"], ["fr", "es"]]
    assert strict_exact_match(gold_seq, pred_seq) == 0.5
    assert sentence_partial_match(gold_seq, pred_seq) == 0.75  # (1.0 + 0.5) / 2

def test_unequal_sentence_counts():
    gold_seq = [["en"]]
    pred_seq = [["en"], ["fr"]]
    with pytest.raises(ValueError, match="Unequal sentence counts"):
        strict_exact_match(gold_seq, pred_seq)
    with pytest.raises(ValueError, match="Unequal sentence counts"):
        sentence_partial_match(gold_seq, pred_seq)
    with pytest.raises(ValueError, match="Unequal sentence counts"):
        boundary_metrics(gold_seq, pred_seq)

def test_unequal_token_counts():
    gold = ["en", "en"]
    pred = ["en"]
    with pytest.raises(ValueError, match="Unequal lengths"):
        token_accuracy(gold, pred)
        
    gold_seq = [["en", "en"]]
    pred_seq = [["en"]]
    # strict_exact_match silently treats it as failed if length != length, wait, the spec says:
    # "A sentence is correct only if the predicted sequence has the same length as the gold sequence... 
    # Reject unequal sentence counts."
    # Wait, the spec for partial match says: "Reject unequal token-sequence lengths instead of silently truncating them."
    # The spec for exact match says: "A sentence is correct only if the predicted sequence has the same length..." Wait, actually it's better if strict_exact_match also rejects unequal lengths if the zip hides them? No, strict_exact_match just requires equal lengths. Wait, I should probably enforce equal lengths strictly in EM as well, or just let my implementation which checks `len(gold) == len(pred)` work. Wait, but `zip(gold_seq, pred_seq)` iterates sentences. Inside the sentence, `len(gold) == len(pred)` is checked. But if zip silently truncates... ah! The regression test requires proving that zip is not allowed to silently truncate!
    with pytest.raises(ValueError, match="Unequal token-sequence lengths"):
        sentence_partial_match(gold_seq, pred_seq)

def test_regression_zip_silent_truncation():
    # If we use zip without checking lengths, it truncates the longer sequence.
    # We must explicitly fail on mismatched token sequence lengths in partial match.
    gold_seq = [["en", "en", "en"]]
    pred_seq = [["en", "en"]]
    with pytest.raises(ValueError, match="Unequal token-sequence lengths"):
        sentence_partial_match(gold_seq, pred_seq)

    with pytest.raises(ValueError, match="Unequal token-label sequence lengths"):
        boundary_metrics(gold_seq, pred_seq)

def test_empty_input():
    assert token_accuracy([], []) == 0.0
    assert strict_exact_match([], []) == 0.0
    assert sentence_partial_match([], []) == 0.0

def test_one_gold_switch_predicted_correctly():
    gold = ["en", "fr"]
    pred = ["en", "fr"]
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 1
    assert bm["false_positives"] == 0
    assert bm["false_negatives"] == 0

def test_missed_boundary():
    gold = ["en", "fr"]
    pred = ["en", "en"]
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 0
    assert bm["false_negatives"] == 1
    assert bm["false_positives"] == 0
    assert bm["boundary_f1"] == 0.0

def test_false_positive_boundary():
    gold = ["en", "en"]
    pred = ["en", "fr"]
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 0
    assert bm["false_positives"] == 1
    assert bm["false_negatives"] == 0
    assert bm["boundary_f1"] == 0.0

def test_boundary_shifted_by_one_token():
    gold = ["en", "en", "fr", "fr"]
    pred = ["en", "fr", "fr", "fr"]
    # Gold boundary at idx 2
    # Pred boundary at idx 1
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 0
    assert bm["false_positives"] == 1
    assert bm["false_negatives"] == 1

def test_ignored_special_labels():
    gold = ["en", "und", "fr"]
    pred = ["en", "und", "fr"]
    # Boundaries would normally be at idx 1 (en->und) and idx 2 (und->fr)
    # If "und" is ignored, these are skipped.
    bm = boundary_metrics([gold], [pred], ignored_labels={"und"})
    assert bm["true_positives"] == 0
    assert bm["total_gold_boundaries"] == 0

def test_sentences_with_no_switches():
    gold = ["en", "en", "en"]
    pred = ["en", "en", "en"]
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 0
    assert bm["false_positives"] == 0
    assert bm["false_negatives"] == 0
    assert bm["boundary_precision"] == 0.0
    assert bm["boundary_recall"] == 0.0
    assert bm["boundary_f1"] == 0.0

def test_multiple_switches():
    gold = ["en", "fr", "en", "fr"]
    pred = ["en", "fr", "en", "fr"]
    bm = boundary_metrics([gold], [pred])
    assert bm["true_positives"] == 3
    assert bm["boundary_f1"] == 1.0

def test_macro_f1_imbalanced_labels():
    gold = ["en", "en", "en", "en", "fr"]
    pred = ["en", "en", "en", "en", "es"]
    metrics = per_language_metrics(gold, pred)
    # en: precision=1.0, recall=1.0, f1=1.0
    # fr: precision=0.0, recall=0.0, f1=0.0
    # es: precision=0.0, recall=0.0, f1=0.0
    assert metrics["per_class"]["en"]["f1"] == 1.0
    assert metrics["per_class"]["fr"]["f1"] == 0.0
    assert metrics["per_class"]["es"]["f1"] == 0.0
    # Macro F1 should be average of 1.0, 0.0, 0.0 = 0.3333
    assert abs(metrics["macro_f1"] - 1.0/3.0) < 1e-6
