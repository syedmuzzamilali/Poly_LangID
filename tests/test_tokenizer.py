import pytest
from polylid import Tokenizer

def simplify(segments):
    return [
        {
            "token": segment[0],
            "script": segment[1],
            "start": segment[2],
            "end": segment[3],
        }
        for segment in segments
    ]

def assert_offsets_match_source(text, segments):
    for token, script, start, end in segments:
        assert text[start:end] == token
        assert 0 <= start <= end <= len(text)

def test_empty_input():
    assert Tokenizer.segment("") == []

def test_whitespace_only():
    assert Tokenizer.segment(" \t\n") == []

def test_english_sentence_offsets():
    text = "Hello world"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
    tokens = [item[0] for item in segments]
    assert tokens == ["Hello", "world"]

def test_mixed_script_sentence():
    text = "Hello, यह एक test है"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
    tokens = [item[0] for item in segments]
    assert "Hello" in tokens
    assert "यह" in tokens
    assert "एक" in tokens
    assert "test" in tokens
    assert "है" in tokens

def test_script_transition_without_space():
    text = "helloहिं"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
    tokens = [item[0] for item in segments]
    assert tokens == ["hello", "हिं"]
    assert segments[0][2:] == (0, 5)
    assert segments[1][2:] == (5, 8)

def test_multiple_script_transitions():
    text = "abcभारतxyz"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
    tokens = [item[0] for item in segments]
    assert tokens == ["abc", "भारत", "xyz"]

def test_punctuation_does_not_break_offsets():
    text = "Hello,world!"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
    tokens = [item[0] for item in segments]
    assert "Hello" in tokens
    assert "world" in tokens

@pytest.mark.parametrize(
    "text",
    [
        "don't stop",
        "state-of-the-art",
        "l'amour",
        "user_name",
        "version2",
        "[email@example.com](mailto:email@example.com)",
    ],
)
def test_internal_delimiters_do_not_corrupt_offsets(text):
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)

@pytest.mark.parametrize(
    "text",
    [
        "!!!",
        "12345",
        "@#$%",
        "🙂🙂",
        "3.14159",
    ],
)
def test_nonlexical_inputs_do_not_crash(text):
    segments = Tokenizer.segment(text)
    assert isinstance(segments, list)
    assert_offsets_match_source(text, segments)

def test_combining_mark_offsets():
    text = "cafe\u0301"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)

def test_zero_width_joiner_input():
    text = "क्\u200dष"
    segments = Tokenizer.segment(text)
    assert_offsets_match_source(text, segments)
