import pytest
from polylid import get_script, dominant_script

@pytest.mark.parametrize(
    "character, expected_script",
    [
        ("A", "LATIN"),
        ("é", "LATIN"),
        ("Ж", "CYRILLIC"),
        ("अ", "DEVANAGARI"),
        ("ب", "ARABIC"),
        ("中", "HAN"),
        ("あ", "HIRAGANA"),
        ("カ", "KATAKANA"),
        ("한", "HANGUL"),
        ("త", "TELUGU"),
        ("த", "TAMIL"),
        ("ક", "GUJARATI"),
        ("গ", "BENGALI"),
        ("ก", "THAI"),
        ("א", "HEBREW"),
        ("ა", "GEORGIAN"),
        ("Ա", "ARMENIAN"),
        ("α", "GREEK"),
    ],
)
def test_character_script_detection(character, expected_script):
    assert get_script(character) == expected_script

@pytest.mark.parametrize(
    "character",
    [" ", ".", ",", "!", "?", "1", "9", "@", "#"],
)
def test_common_characters(character):
    result = get_script(character)
    assert result in {
        "COMMON",
        "INHERITED",
        "UNKNOWN",
        None,
    }

@pytest.mark.parametrize(
    "token, expected",
    [
        ("hello", "LATIN"),
        ("भारत", "DEVANAGARI"),
        ("తెలుగు", "TELUGU"),
        ("தமிழ்", "TAMIL"),
        ("العربية", "ARABIC"),
        ("русский", "CYRILLIC"),
        ("中文", "HAN"),
    ],
)
def test_dominant_script(token, expected):
    assert dominant_script(token) == expected
