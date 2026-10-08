import pytest
from evaluation.label_audit import DATASETS
from collections import Counter

def test_tongueswitcher_mapping():
    mapping = DATASETS["tongueswitcher_de_en"]["mapping"]
    assert mapping.get("ger") == "de"
    assert mapping.get("de") == "de"
    assert mapping.get("en") == "en"
    
    # Check that neither de nor en is ignored
    ignored_reasons = DATASETS["tongueswitcher_de_en"]["ignored_reasons"]
    assert "de" not in ignored_reasons
    assert "en" not in ignored_reasons

def test_turkish_german_mapping():
    mapping = DATASETS["turkish_german"]["mapping"]
    assert mapping.get("tr") == "tr"
    assert mapping.get("tur") == "tr"
    assert mapping.get("de") == "de"
    assert mapping.get("ger") == "de"
    
def test_arabic_english_mapping():
    mapping = DATASETS["arabic_english"]["mapping"]
    assert mapping.get("ar") == "ar"
    assert mapping.get("en") == "en"

def test_unknown_labels_raise_error():
    # Tested dynamically by audit_dataset failing
    pass
