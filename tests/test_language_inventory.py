from polylid import SUPPORTED_LANGS

EXPECTED_LANGUAGES = {
    "af", "sq", "ar", "hy", "az", "eu", "be", "bn",
    "bs", "bg", "ca", "zh", "hr", "cs", "da", "nl",
    "en", "eo", "et", "fi", "fr", "ka", "de", "el",
    "gu", "he", "hi", "hu", "is", "id", "ga", "it",
    "ja", "kk", "ko", "la", "lv", "lt", "mk", "ms",
    "mr", "nn", "fa", "pl", "pt", "pa", "ro", "ru",
    "sr", "sk", "sl", "so", "es", "sw", "sv", "tl",
    "ta", "te", "th", "tr", "uk", "ur", "vi", "cy",
    "yo",
}

def test_supported_language_count():
    assert len(SUPPORTED_LANGS) == 65

def test_supported_language_inventory():
    assert set(SUPPORTED_LANGS) == EXPECTED_LANGUAGES

def test_no_duplicate_language_codes():
    assert len(SUPPORTED_LANGS) == len(set(SUPPORTED_LANGS))

def test_language_codes_are_lowercase():
    assert all(code == code.lower() for code in SUPPORTED_LANGS)

def test_language_codes_have_two_characters():
    assert all(len(code) == 2 for code in SUPPORTED_LANGS)

def test_bulgarian_is_present():
    assert "bg" in SUPPORTED_LANGS
