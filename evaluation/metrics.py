from typing import List, Sequence, Set, Tuple, Dict, Any, Optional
from collections import Counter

EXPECTED_DATASET_LABELS = {
    "chinese_english": ("en", "zh"),
    "arabic_english": ("ar", "en"),
    "indonesian_english": ("en", "id"),
    "tongueswitcher_de_en": ("de", "en"),
    "turkish_german": ("de", "tr"),
    "lince_spaeng": ("en", "es"),
    "lince_turen": ("en", "tr"),
}

def validate_dataset_labels(dataset_name: str, gold_labels: Sequence[str]) -> Tuple[str, ...]:
    if dataset_name not in EXPECTED_DATASET_LABELS:
        raise ValueError(f"Unknown dataset name: {dataset_name}")
        
    expected = set(EXPECTED_DATASET_LABELS[dataset_name])
    observed = set(gold_labels)
    
    missing = expected - observed
    unexpected = observed - expected
    
    if missing:
        raise ValueError(
            f"{dataset_name}: missing expected gold labels "
            f"{sorted(missing)}; counts={Counter(gold_labels)}"
        )
        
    if unexpected:
        raise ValueError(
            f"{dataset_name}: unexpected evaluated labels "
            f"{sorted(unexpected)}; counts={Counter(gold_labels)}"
        )
        
    return EXPECTED_DATASET_LABELS[dataset_name]

def token_accuracy(gold: Sequence[str], predicted: Sequence[str]) -> float:
    if len(gold) != len(predicted):
        raise ValueError(f"Unequal lengths: gold={len(gold)}, predicted={len(predicted)}")
    if not gold:
        return 0.0
    correct = sum(1 for g, p in zip(gold, predicted) if g == p)
    return correct / len(gold)

def strict_exact_match(gold_sequences: Sequence[Sequence[str]], predicted_sequences: Sequence[Sequence[str]]) -> float:
    if len(gold_sequences) != len(predicted_sequences):
        raise ValueError("Unequal sentence counts")
    if not gold_sequences:
        return 0.0
    correct_sentences = 0
    for gold, pred in zip(gold_sequences, predicted_sequences):
        if len(gold) == len(pred) and all(g == p for g, p in zip(gold, pred)):
            correct_sentences += 1
    return correct_sentences / len(gold_sequences)

def sentence_partial_match(gold_sequences: Sequence[Sequence[str]], predicted_sequences: Sequence[Sequence[str]]) -> float:
    if len(gold_sequences) != len(predicted_sequences):
        raise ValueError("Unequal sentence counts")
    if not gold_sequences:
        return 0.0
    total_score = 0.0
    for gold, pred in zip(gold_sequences, predicted_sequences):
        if len(gold) != len(pred):
            raise ValueError("Unequal token-sequence lengths")
        if not gold:
            # Empty sequences don't contribute positively to agreement, but we shouldn't throw error
            continue
        correct = sum(1 for g, p in zip(gold, pred) if g == p)
        total_score += correct / len(gold)
    return total_score / len(gold_sequences)

def switch_boundaries(labels: Sequence[str], ignored_labels: Optional[Set[str]] = None) -> Set[int]:
    ignored = ignored_labels or set()
    boundaries = set()
    for i in range(1, len(labels)):
        if labels[i] in ignored or labels[i-1] in ignored:
            continue
        if labels[i] != labels[i-1]:
            boundaries.add(i)
    return boundaries

def boundary_metrics(gold_sequences: Sequence[Sequence[str]], predicted_sequences: Sequence[Sequence[str]], ignored_labels: Optional[Set[str]] = None) -> Dict[str, float]:
    if len(gold_sequences) != len(predicted_sequences):
        raise ValueError("Unequal sentence counts")
    
    tp = fp = fn = 0
    total_gold_boundaries = 0
    total_pred_boundaries = 0
    
    for gold, pred in zip(gold_sequences, predicted_sequences):
        if len(gold) != len(pred):
            raise ValueError("Unequal token-label sequence lengths")
            
        gold_b = switch_boundaries(gold, ignored_labels)
        pred_b = switch_boundaries(pred, ignored_labels)
        
        total_gold_boundaries += len(gold_b)
        total_pred_boundaries += len(pred_b)
        
        tp += len(gold_b & pred_b)
        fp += len(pred_b - gold_b)
        fn += len(gold_b - pred_b)
        
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "boundary_precision": precision,
        "boundary_recall": recall,
        "boundary_f1": f1,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "total_gold_boundaries": total_gold_boundaries,
        "total_pred_boundaries": total_pred_boundaries
    }

def per_language_metrics(gold: Sequence[str], predicted: Sequence[str], labels: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    if len(gold) != len(predicted):
        raise ValueError("Unequal lengths")
    
    if labels is None:
        labels = sorted(list(set(gold) | set(predicted)))
    else:
        labels = list(labels)
    
    tp = Counter()
    fp = Counter()
    fn = Counter()
    support = Counter()
    
    # We may encounter predictions outside the allowed labels. We should track those
    # in `fp` for the predicted class, but only include them in the confusion matrix 
    # and per_class dictionary if they are in `labels`.
    
    cm = [[0] * len(labels) for _ in range(len(labels))]
    label_to_idx = {l: i for i, l in enumerate(labels)}
    
    for g, p in zip(gold, predicted):
        support[g] += 1
        
        if g in label_to_idx and p in label_to_idx:
            cm[label_to_idx[g]][label_to_idx[p]] += 1
            
        if g == p:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1
            
    per_class = {}
    macro_f1_sum = 0.0
    weighted_f1_sum = 0.0
    
    # We only care about support among the *expected* labels for the dataset
    total_expected_support = sum(support[l] for l in labels)
    
    for label in labels:
        _tp = tp[label]
        _fp = fp[label]
        _fn = fn[label]
        _supp = support[label]
        
        prec = _tp / (_tp + _fp) if (_tp + _fp) > 0 else 0.0
        rec = _tp / (_tp + _fn) if (_tp + _fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        per_class[label] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": _supp
        }
        
        macro_f1_sum += f1
        weighted_f1_sum += f1 * _supp
        
    macro_f1 = macro_f1_sum / len(labels) if labels else 0.0
    weighted_f1 = weighted_f1_sum / total_expected_support if total_expected_support > 0 else 0.0
        
    return {
        "per_class": per_class,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "confusion_matrix": cm,
        "labels": labels
    }
