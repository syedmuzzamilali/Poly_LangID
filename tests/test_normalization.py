import math
import pytest
from polylid import normalize_lang_code, normalize_probs, top_label

@pytest.mark.parametrize(
    "raw_code, expected",
    [
        ("EN", "en"),
        ("en", "en"),
        ("eng", "en"),
        ("en-US", "en"),
        ("en_US", "en"),
        ("zh-CN", "zh"),
        ("zh_TW", "zh"),
        ("fra", "fr"),
        ("fre", "fr"),
        ("deu", "de"),
        ("ger", "de"),
        ("fas", "fa"),
        ("per", "fa"),
        ("zho", "zh"),
        ("chi", "zh"),
    ],
)
def test_known_language_aliases(raw_code, expected):
    assert normalize_lang_code(raw_code) == expected

@pytest.mark.parametrize(
    "raw_code",
    [
        "",
        None,
        "unknown",
        "123",
        "xx",
        "__label__unknown",
    ],
)
def test_invalid_language_codes(raw_code):
    result = normalize_lang_code(raw_code)
    assert result is None or result not in {"unknown", "xx"}

def test_fasttext_label_prefix():
    assert normalize_lang_code("__label__en") == "en"

def test_probability_normalization():
    raw = {
        "en": 0.60,
        "es": 0.30,
        "xx": 0.10,
    }
    result = normalize_probs(raw, {"en", "es"})
    assert set(result) == {"en", "es"}
    assert math.isclose(sum(result.values()), 1.0, rel_tol=1e-9)

def test_empty_probability_distribution():
    result = normalize_probs({}, {"en", "es"})
    assert result == {}

def test_zero_probability_distribution():
    raw = {
        "en": 0.0,
        "es": 0.0,
    }
    result = normalize_probs(raw, {"en", "es"})
    assert result == {} or sum(result.values()) == 0.0

def test_negative_probabilities_are_rejected():
    raw = {
        "en": 0.8,
        "es": -0.2,
    }
    result = normalize_probs(raw, {"en", "es"})
    assert all(value >= 0.0 for value in result.values())

def test_candidate_restriction():
    raw = {
        "en": 0.5,
        "es": 0.3,
        "fr": 0.2,
    }
    result = normalize_probs(raw, {"en", "es"})
    assert "fr" not in result
    assert set(result) == {"en", "es"}

def test_top_label_and_margin():
    distribution = {
        "en": 0.70,
        "es": 0.20,
        "fr": 0.10,
    }
    label, confidence, margin = top_label(distribution)
    assert label == "en"
    assert math.isclose(confidence, 0.70)
    assert math.isclose(margin, 0.50)

def test_tied_distribution():
    distribution = {
        "en": 0.50,
        "es": 0.50,
    }
    label, confidence, margin = top_label(distribution)
    assert label in {"en", "es"}
    assert math.isclose(confidence, 0.50)
    assert math.isclose(margin, 0.0)

def test_single_candidate_margin():
    distribution = {
        "en": 1.0,
    }
    label, confidence, margin = top_label(distribution)
    assert label == "en"
    assert math.isclose(confidence, 1.0)
    assert margin in {1.0, 0.0}

def test_empty_distribution():
    result = top_label({})
    assert result is None or result[0] is None
