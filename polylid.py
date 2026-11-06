from __future__ import annotations

import importlib
import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# ==============================================================================
# 1. LANGUAGE INVENTORY & SCRIPT TOPOLOGY
# ==============================================================================

SUPPORTED_LANGS = {
    # European / Western
    "en", "es", "tr", "fr", "de", "it", "pt", "nl", "pl", "ru", "uk", "cs", "el", "ro", "sv",
    "da", "fi", "hu", "nn", "sk", "sl", "hr", "sr", "bs", "ca", "eu", "et", "lv", "lt",
    "is", "ga", "cy", "la", "eo", "sq", "mk", "be",
    # Middle Eastern
    "ar", "ur", "fa", "he",
    # East & Southeast Asian
    "zh", "ja", "ko", "th", "vi", "id", "ms", "tl", "mn",
    # South Asian / Indic
    "hi", "bn", "mr", "pa", "gu", "ta", "te",
    # African / Others
    "af", "sw", "yo", "so", "az", "hy", "ka", "kk", "bg"
}

NO_SPACE_SCRIPTS = {"HAN", "HIRAGANA", "KATAKANA", "HANGUL", "THAI"}

SCRIPT_RANGES = {
    "HAN": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF)],
    "HIRAGANA": [(0x3040, 0x309F)],
    "KATAKANA": [(0x30A0, 0x30FF), (0x31F0, 0x31FF)],
    "HANGUL": [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],
    "THAI": [(0x0E00, 0x0E7F)],
    "ARABIC": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "DEVANAGARI": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "BENGALI": [(0x0980, 0x09FF)],
    "GUJARATI": [(0x0A80, 0x0AFF)],
    "GURMUKHI": [(0x0A00, 0x0A7F)],
    "KANNADA": [(0x0C80, 0x0CFF)],
    "MALAYALAM": [(0x0D00, 0x0D7F)],
    "ORIYA": [(0x0B00, 0x0B7F)],
    "TAMIL": [(0x0B80, 0x0BFF)],
    "TELUGU": [(0x0C00, 0x0C7F)],
    "CYRILLIC": [(0x0400, 0x04FF), (0x0500, 0x052F)],
    "GREEK": [(0x0370, 0x03FF)],
    "HEBREW": [(0x0590, 0x05FF)],
    "GEORGIAN": [(0x10A0, 0x10FF), (0x2D00, 0x2D2F)],
    "ARMENIAN": [(0x0530, 0x058F)],
    "LATIN": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F), (0x1E00, 0x1EFF)],
}

SCRIPT_TO_DEFAULT_LANG = {
    "GUJARATI": "gu", "GURMUKHI": "pa", "TAMIL": "ta", "TELUGU": "te", "THAI": "th",
    "HANGUL": "ko", "HIRAGANA": "ja", "KATAKANA": "ja", "HAN": "zh",
    "GREEK": "el", "HEBREW": "he", "GEORGIAN": "ka", "ARMENIAN": "hy",
}

SINGLETON_SCRIPTS = {
    "GUJARATI": "gu", "GURMUKHI": "pa", "TAMIL": "ta", "TELUGU": "te", "THAI": "th",
    "HANGUL": "ko", "HIRAGANA": "ja", "KATAKANA": "ja",
    "GREEK": "el", "HEBREW": "he", "GEORGIAN": "ka", "ARMENIAN": "hy", "BENGALI": "bn"
}

SCRIPT_TO_LANGUAGES = {
    "BENGALI": {"bn"}, "DEVANAGARI": {"hi", "mr"}, "ARABIC": {"ar", "ur", "fa"},
    "CYRILLIC": {"ru", "bg", "uk", "be", "sr", "mk", "kk", "mn"},
    "LATIN": {"en", "es", "tr", "fr", "de", "it", "pt", "nl", "pl", "cs", "ro", "sv", "vi", "id", "ms", "da", "fi", "hu", "sk", "sl", "hr", "ca", "eu", "et", "lv", "lt", "is", "ga", "cy", "la", "eo", "sq", "af", "sw", "so", "yo", "az", "tl", "nn", "bs"},
    "HAN": {"zh", "ja"}, "HIRAGANA": {"ja"}, "KATAKANA": {"ja"}, "HANGUL": {"ko"},
    "THAI": {"th"}, "GUJARATI": {"gu"}, "GURMUKHI": {"pa"}, "KANNADA": set(),
    "MALAYALAM": set(), "ORIYA": set(), "TAMIL": {"ta"}, "TELUGU": {"te"},
    "GREEK": {"el"}, "HEBREW": {"he"}, "GEORGIAN": {"ka"}, "ARMENIAN": {"hy"},
}

LANG_NAME_TO_CODE = {
    "arabic": "ar", "bulgarian": "bg", "bengali": "bn", "bangla": "bn", "german": "de",
    "english": "en", "spanish": "es", "french": "fr", "gujarati": "gu",
    "hindi": "hi", "indonesian": "id", "italian": "it", "japanese": "ja",
    "korean": "ko", "dutch": "nl", "polish": "pl", "portuguese": "pt",
    "russian": "ru", "tamil": "ta", "telugu": "te", "thai": "th", "turkish": "tr",
    "urdu": "ur", "vietnamese": "vi", "chinese": "zh", "mandarin": "zh",
    "marathi": "mr", "punjabi": "pa", "persian": "fa", "farsi": "fa",
    "greek": "el", "hebrew": "he", "romanian": "ro", "swedish": "sv", "czech": "cs",
    "ukrainian": "uk", "danish": "da", "finnish": "fi", "hungarian": "hu",
    "slovak": "sk", "slovene": "sl", "catalan": "ca", "basque": "eu", "croatian": "hr",
    "serbian": "sr", "estonian": "et", "latvian": "lv", "lithuanian": "lt",
    "icelandic": "is", "irish": "ga", "welsh": "cy", "latin": "la", "esperanto": "eo",
    "albanian": "sq", "macedonian": "mk", "belarusian": "be", "afrikaans": "af",
    "swahili": "sw", "somali": "so", "yoruba": "yo",
    "azerbaijani": "az", "georgian": "ka", "armenian": "hy", "kazakh": "kk",
    "malay": "ms", "tagalog": "tl", "mongolian": "mn", "nynorsk": "nn", "bosnian": "bs"
}

LINGUA_LANG_MAP = {
    "ARABIC": "ar", "BULGARIAN": "bg", "BENGALI": "bn", "GERMAN": "de",
    "ENGLISH": "en", "SPANISH": "es", "FRENCH": "fr", "GUJARATI": "gu",
    "HINDI": "hi", "INDONESIAN": "id", "ITALIAN": "it", "JAPANESE": "ja",
    "KOREAN": "ko", "DUTCH": "nl", "POLISH": "pl", "PORTUGUESE": "pt",
    "RUSSIAN": "ru", "TAMIL": "ta", "TELUGU": "te", "THAI": "th", "TURKISH": "tr",
    "URDU": "ur", "VIETNAMESE": "vi", "CHINESE": "zh", "MARATHI": "mr", "PUNJABI": "pa",
    "PERSIAN": "fa", "HEBREW": "he", "GREEK": "el", "ROMANIAN": "ro",
    "SWEDISH": "sv", "CZECH": "cs", "UKRAINIAN": "uk", "DANISH": "da",
    "FINNISH": "fi", "HUNGARIAN": "hu", "SLOVAK": "sk", "SLOVENE": "sl",
    "CATALAN": "ca", "BASQUE": "eu", "CROATIAN": "hr", "SERBIAN": "sr",
    "ESTONIAN": "et", "LATVIAN": "lv", "LITHUANIAN": "lt", "ICELANDIC": "is",
    "IRISH": "ga", "WELSH": "cy", "LATIN": "la", "ESPERANTO": "eo",
    "ALBANIAN": "sq", "MACEDONIAN": "mk", "BELARUSIAN": "be", "AFRIKAANS": "af",
    "SWAHILI": "sw", "SOMALI": "so", "YORUBA": "yo",
    "AZERBAIJANI": "az", "GEORGIAN": "ka", "ARMENIAN": "hy", "KAZAKH": "kk",
    "MALAY": "ms", "TAGALOG": "tl", "BOSNIAN": "bs", "NYNORSK": "nn", "MONGOLIAN": "mn"
}

GLOTLID_SNAPSHOT = "85cd6716494360367b75f642b5bc78667605d0b4"

GLOTLID_MAP = {
    'eng': 'en', 'spa': 'es', 'por': 'pt', 'fra': 'fr', 'ita': 'it', 
    'deu': 'de', 'tur': 'tr', 'zho': 'zh', 'cmn': 'zh', 'hin': 'hi', 
    'rus': 'ru', 'jpn': 'ja', 'kor': 'ko', 'ind': 'id', 'nld': 'nl',
    'pol': 'pl', 'ben': 'bn', 'tam': 'ta', 'tel': 'te', 'guj': 'gu',
    'tha': 'th', 'vie': 'vi', 'ara': 'ar', 'arb': 'ar', 'bul': 'bg',
    'urd': 'ur', 'mar': 'mr', 'pan': 'pa',
    'fas': 'fa', 'pes': 'fa', 'ell': 'el', 'heb': 'he', 'ron': 'ro',
    'swe': 'sv', 'ces': 'cs', 'ukr': 'uk', 'dan': 'da', 'fin': 'fi',
    'hun': 'hu', 'slk': 'sk', 'slv': 'sl', 'cat': 'ca', 'eus': 'eu',
    'hrv': 'hr', 'srp': 'sr', 'est': 'et', 'lav': 'lv', 'lit': 'lt',
    'isl': 'is', 'gle': 'ga', 'cym': 'cy', 'lat': 'la', 'epo': 'eo',
    'sqi': 'sq', 'mkd': 'mk', 'bel': 'be', 'afr': 'af', 'swh': 'sw',
    'som': 'so', 'yor': 'yo', 'azj': 'az',
    'kat': 'ka', 'hye': 'hy', 'kaz': 'kk', 'zsm': 'ms', 'tgl': 'tl',
    'bos': 'bs', 'nno': 'nn', 'khk': 'mn', 'mon': 'mn'
}

# ==============================================================================
# 2. HELPER FUNCTIONS & SCRIPT REASONER
# ==============================================================================

@lru_cache(maxsize=32768)
def get_script(ch: str) -> str:
    code = ord(ch)
    # Fast path for common ASCII Latin characters
    if (65 <= code <= 90) or (97 <= code <= 122) or (0x00C0 <= code <= 0x024F) or (0x1E00 <= code <= 0x1EFF):
        return "LATIN"
    # Fast path for East Asian scripts
    if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0x20000 <= code <= 0x2A6DF:
        return "HAN"
    if 0x3040 <= code <= 0x309F:
        return "HIRAGANA"
    if 0x30A0 <= code <= 0x30FF or 0x31F0 <= code <= 0x31FF:
        return "KATAKANA"
    if 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F:
        return "HANGUL"
    # Fast path for Middle Eastern & Indic scripts
    if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F or 0x08A0 <= code <= 0x08FF or 0xFB50 <= code <= 0xFDFF or 0xFE70 <= code <= 0xFEFF:
        return "ARABIC"
    if 0x0900 <= code <= 0x097F or 0xA8E0 <= code <= 0xA8FF:
        return "DEVANAGARI"
    if 0x0400 <= code <= 0x04FF or 0x0500 <= code <= 0x052F:
        return "CYRILLIC"
    if 0x0E00 <= code <= 0x0E7F:
        return "THAI"
    if 0x0980 <= code <= 0x09FF:
        return "BENGALI"
    if 0x0A80 <= code <= 0x0AFF:
        return "GUJARATI"
    if 0x0A00 <= code <= 0x0A7F:
        return "GURMUKHI"
    if 0x0B80 <= code <= 0x0BFF:
        return "TAMIL"
    if 0x0C00 <= code <= 0x0C7F:
        return "TELUGU"
    if 0x0C80 <= code <= 0x0CFF:
        return "KANNADA"
    if 0x0D00 <= code <= 0x0D7F:
        return "MALAYALAM"
    if 0x0B00 <= code <= 0x0B7F:
        return "ORIYA"
    if 0x0370 <= code <= 0x03FF:
        return "GREEK"
    if 0x0590 <= code <= 0x05FF:
        return "HEBREW"
    if 0x10A0 <= code <= 0x10FF or 0x2D00 <= code <= 0x2D2F:
        return "GEORGIAN"
    if 0x0530 <= code <= 0x058F:
        return "ARMENIAN"
    return "OTHER"

def dominant_script(text: str) -> str:
    votes = Counter()
    for ch in text:
        if ch.isalpha():
            script = get_script(ch)
            if script != "OTHER":
                votes[script] += 1
    return votes.most_common(1)[0][0] if votes else "OTHER"

def normalize_lang_code(code: str) -> str:
    value = str(code or "").strip().lower().replace("__label__", "").replace("_", "-")
    if not value:
        return ""
    alias = {
        "zh-cn": "zh", "zh-tw": "zh", "zh-hans": "zh", "zh-hant": "zh", "jp": "ja",
        "jpn": "ja", "ko-kr": "ko", "pt-br": "pt", "guj": "gu", "hin": "hi",
        "mar": "mr", "nep": "ne", "pan": "pa", "tam": "ta", "tel": "te", "urd": "ur",
        "eng": "en", "spa": "es", "tur": "tr", "arb": "ar", "fra": "fr", "deu": "de",
        "ita": "it", "por": "pt", "rus": "ru", "bul": "bg", "zho": "zh", "cmn": "zh",
        "vie": "vi", "tha": "th", "ind": "id", "nld": "nl", "pol": "pl", "other": "und",
        "dty": "ne", "dot": "ne", "npi": "ne", "nob": "nb", "nno": "nn", "zsm": "ms",
        "kan": "kn", "mal": "ml", "ory": "or", "asm": "as", "san": "sa", "snd": "sd", "fre": "fr", "ger": "de", "fas": "fa", "per": "fa", "chi": "zh"
    }
    if value in alias:
        return alias[value]
    if value in SUPPORTED_LANGS:
        return value
    if value in LANG_NAME_TO_CODE:
        return LANG_NAME_TO_CODE[value]
    head = value.split("-", 1)[0]
    return alias.get(head, head if head in SUPPORTED_LANGS else LANG_NAME_TO_CODE.get(head, ""))

def _resolve_asset_path(rel_path: str) -> str:
    if os.path.exists(rel_path):
        return rel_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(base_dir, rel_path)
    return abs_path if os.path.exists(abs_path) else rel_path

def require(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None

def normalize_probs(dist: Dict[str, float], allowed_langs=None) -> Dict[str, float]:
    allowed_set = set(allowed_langs) if allowed_langs is not None else SUPPORTED_LANGS
    filtered = {k: float(v) for k, v in dist.items() if v > 0 and k in allowed_set}
    total = sum(filtered.values())
    return {k: v / total for k, v in filtered.items()} if total > 0 else {}

def top_label(dist: Dict[str, float]) -> Tuple[str, float, float]:
    if not dist:
        return None, 0.0, 0.0
    ranked = sorted(dist.items(), key=lambda item: item[1], reverse=True)
    best_lang, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    return best_lang, float(best_score), float(best_score - second_score)

# ==============================================================================
# 3. LANGUAGE MODELS
# ==============================================================================

class CandidateGenerator:
    @classmethod
    def project_distribution(cls, dist: Dict[str, float], allowed: Iterable[str]) -> Dict[str, float]:
        if allowed is None:
            return normalize_probs(dist)
        allowed_set = set(allowed)
        filtered = {k: v for k, v in dist.items() if k in allowed_set}
        return normalize_probs(filtered)

    @classmethod
    def generate_candidates(cls, allowed_langs: Iterable[str] = None) -> set[str]:
        """Return the open-world language inventory (66 supported languages).
        
        PolyLID operates strictly in open-world mode: candidate sets are dynamically
        self-determined per input sequence via CandidateDetector rather than supplied externally.
        """
        return SUPPORTED_LANGS

    @classmethod
    def get_candidates(cls, allowed_langs: Iterable[str] = None) -> set[str]:
        return cls.generate_candidates(allowed_langs)


@dataclass
class ModelPrediction:
    label: str
    confidence: float
    margin: float
    ranked_candidates: List[Tuple[str, float]]
    model: str
    raw_dist: Dict[str, float]
    res_dist: Dict[str, float]


@dataclass
class PredictionEvidence:
    model: str
    prediction: ModelPrediction
    margin: float
    confidence: float
    boundary: Any
    agreement_count: int
    script: str
    token: str
    raw_candidates: List[Tuple[str, float]]


class DecisionStage(str, Enum):
    DETERMINISTIC_SCRIPT = "Deterministic Script Prior"
    UNANIMOUS = "Unanimous Agreement"
    CONSENSUS = "Consensus"
    LOCAL_CONTEXT = "Local Context"
    EVIDENCE_COMPARISON = "Evidence Comparison"
    CONTEXT_REFINEMENT = "Context Refinement"
    NO_MODELS = "No Active Models"


@dataclass
class DecisionTrace:
    token: str
    model_predictions: Dict[str, str]
    selected_model: str
    decision_stage: str
    reasoning: str


@dataclass
class TokenDecision:
    label: str
    decided_by: str
    reason: str
    competing_predictions: List[Tuple[str, str]]
    distribution: Dict[str, float]
    trace: Optional[DecisionTrace] = None

    @classmethod
    def create_with_trace(
        cls,
        label: str,
        decided_by: str,
        reason: str,
        competing_predictions: List[Tuple[str, str]],
        distribution: Dict[str, float],
        token: str,
        model_predictions: Dict[str, str],
        decision_stage: DecisionStage,
    ) -> "TokenDecision":
        trace = DecisionTrace(
            token=token,
            model_predictions=model_predictions,
            selected_model=decided_by,
            decision_stage=decision_stage,
            reasoning=reason,
        )
        return cls(label, decided_by, reason, competing_predictions, distribution, trace)

    @property
    def margin(self) -> float:
        if not self.distribution:
            return 0.0
        vals = sorted(self.distribution.values(), reverse=True)
        return (vals[0] - vals[1]) if len(vals) >= 2 else (vals[0] if vals else 0.0)


@dataclass
class BoundaryEvidence:
    script_changed: bool
    models_disagree: bool
    is_switch_point: bool
    needs_arbitration: bool


class BaseLanguageModel:
    def __init__(self, name: str):
        self.name = name
        self._cache: Dict[str, Dict[str, float]] = {}

    def supports_token(self, token: str, script: str, allowed_langs: Iterable[str] = None) -> bool:
        return bool(token and token.strip())

    def predict(self, text: str, allowed: Iterable[str]) -> Dict[str, float]:
        raise NotImplementedError

    def evaluate(self, text: str, allowed: Iterable[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        restricted = self.predict(text, allowed)
        key = unicodedata.normalize("NFC", text or "").casefold()
        raw = self._cache.get(key, restricted)
        return raw, restricted

    def _restrict(self, dist: Dict[str, float], allowed: Iterable[str]) -> Dict[str, float]:
        return CandidateGenerator.project_distribution(dist, allowed)


class FastTextModel(BaseLanguageModel):
    def __init__(self, ft_path: str = "lid.176.ftz"):
        super().__init__("FastText")
        self.model = None
        ft_mod = require("fasttext")
        resolved_path = _resolve_asset_path(ft_path)
        if ft_mod is not None and os.path.exists(resolved_path):
            try:
                self.model = ft_mod.load_model(resolved_path)
            except Exception:
                self.model = None

    def predict(self, text: str, allowed: Iterable[str]) -> Dict[str, float]:
        key = unicodedata.normalize("NFC", text or "").casefold()
        if key in self._cache:
            return self._restrict(self._cache[key], allowed)
        if self.model is None or not text.strip():
            self._cache[key] = {}
            return {}
        try:
            text_cln = text.replace('\n', ' ') + '\n'
            predictions = self.model.f.predict(text_cln, 12, 0.0, "strict")
            raw = {normalize_lang_code(l): float(p) for p, l in predictions if normalize_lang_code(l)} if predictions else {}
            dist = normalize_probs(raw)
            # Temperature scaling for short tokens (<= 4 chars) to soften uncalibrated peaky softmax
            tok_len = len(text.strip())
            if tok_len <= 4 and dist:
                T = 1.35
                scaled = {l: math.exp(math.log(max(p, 1e-7)) / T) for l, p in dist.items()}
                dist = normalize_probs(scaled)
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)


class GlotLIDModel(BaseLanguageModel):
    def __init__(self):
        super().__init__("GlotLID")
        self.model = None
        ft_mod = require("fasttext")
        if ft_mod is not None:
            hf_cache = os.path.expanduser("~/.cache/huggingface/hub/models--cis-lmu--glotlid/snapshots")
            glotlid_path = os.path.join(hf_cache, GLOTLID_SNAPSHOT, "model.bin")
            if not os.path.exists(glotlid_path):
                raise FileNotFoundError(f"Required GlotLID snapshot missing: {glotlid_path}")
            self.model = ft_mod.load_model(glotlid_path)

    def predict(self, text: str, allowed: Iterable[str]) -> Dict[str, float]:
        key = unicodedata.normalize("NFC", text or "").casefold()
        if key in self._cache:
            return self._restrict(self._cache[key], allowed)
        if self.model is None or not text.strip():
            self._cache[key] = {}
            return {}
        try:
            text_cln = text.replace('\n', ' ') + '\n'
            predictions = self.model.f.predict(text_cln, 15, 0.0, "strict")
            raw = {}
            if predictions:
                for p, l in predictions:
                    iso3 = l.replace('__label__', '').split('_')[0]
                    code = GLOTLID_MAP.get(iso3, normalize_lang_code(iso3))
                    if code:
                        raw[code] = raw.get(code, 0.0) + float(p)
            dist = normalize_probs(raw)
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)


class LinguaModel(BaseLanguageModel):
    def __init__(self):
        super().__init__("Lingua")
        self.model = None
        lingua_mod = require("lingua")
        if lingua_mod is not None:
            try:
                Language = getattr(lingua_mod, "Language")
                Builder = getattr(lingua_mod, "LanguageDetectorBuilder")
                langs = [
                    getattr(Language, name)
                    for name, code in LINGUA_LANG_MAP.items()
                    if hasattr(Language, name)
                ]
                self.model = Builder.from_languages(*langs).build() if langs else None
            except Exception:
                self.model = None

    def predict(self, text: str, allowed: Iterable[str]) -> Dict[str, float]:
        key = unicodedata.normalize("NFC", text or "").casefold()
        if key in self._cache:
            return self._restrict(self._cache[key], allowed)
        if self.model is None or not text.strip():
            self._cache[key] = {}
            return {}
        try:
            confs = self.model.compute_language_confidence_values(text)
            raw = {}
            for conf in confs[:12]:
                lang = LINGUA_LANG_MAP.get(str(conf.language).split(".")[-1].upper().strip(), "")
                if lang:
                    raw[lang] = max(raw.get(lang, 0.0), float(conf.value))
            dist = normalize_probs(raw)
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)


# ==============================================================================
# 4. PIPELINE COMPONENTS
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. TOKENIZER: Text segmentation & Unicode script annotation
# ------------------------------------------------------------------------------
URL_REGEX = re.compile(r'(?:https?://|www\.)\S+|t\.co/\S+', re.IGNORECASE)
MENTION_REGEX = re.compile(r'@\w+')
INTERNAL_PUNCTUATION = {"'", "’", "-"}
CLAUSE_BREAKS = {
    ".", ",", "!", "?", ";", ":", "—", "–", "-", "\n", "|", "/", "\\",
    "(", ")", "[", "]", "{", "}", "\"", "'", "«", "»", "“", "”", "„", "§",
    "،", "؛", "؟", "۔", "¡", "¿",
    "，", "、", "。", "；", "：", "！", "？"
}
STRIP_CHARACTERS = '.,!?;:"\'()[]{}—،؛؟۔¡¿，、。；：！？|'


class Tokenizer:
    @staticmethod
    def _segment_text_tokens(text: str, base_offset: int = 0) -> List[Tuple[str, str, int, int]]:
        if not text:
            return []
        parts = []
        buf = []
        last_script = ""
        start_idx = 0
        
        for i, ch in enumerate(text):
            category = unicodedata.category(ch)
            is_internal_punc = (
                ch in INTERNAL_PUNCTUATION
                and 0 < i < len(text) - 1
                and text[i - 1].isalnum()
                and text[i + 1].isalnum()
            )
            is_sep = not is_internal_punc and (ch.isspace() or category.startswith("P") or category.startswith("S"))
            script = get_script(ch)
            
            if is_sep:
                if buf:
                    span_str = "".join(buf)
                    parts.append((span_str, dominant_script(span_str), start_idx, i))
                    buf = []
                last_script = ""
                continue
                
            if buf and last_script and script != "OTHER" and last_script != "OTHER" and script != last_script:
                span_str = "".join(buf)
                parts.append((span_str, dominant_script(span_str), start_idx, i))
                buf = [ch]
                start_idx = i
            else:
                if not buf:
                    start_idx = i
                buf.append(ch)
            if script != "OTHER":
                last_script = script
                
        if buf:
            span_str = "".join(buf)
            parts.append((span_str, dominant_script(span_str), start_idx, len(text)))
            
        segments = [
            p for p in parts
            if isinstance(p[0], str) and (any(c.isalpha() for c in p[0]) or any(c.isdigit() for c in p[0]))
        ]

        # Sub-token script boundary splitting
        new_segments = []
        for tok, script, start, end in segments:
            if script in ("HAN", "HIRAGANA", "KATAKANA", "HANGUL", "THAI") and len(tok) > 1:
                sub_parts = []
                cur_sc, cur_buf, cur_st = None, [], start
                for idx_ch, ch in enumerate(tok):
                    ch_sc = get_script(ch)
                    if cur_sc is None:
                        cur_sc = ch_sc
                        cur_buf.append(ch)
                    elif ch_sc == cur_sc:
                        cur_buf.append(ch)
                    else:
                        sub_str = "".join(cur_buf)
                        sub_parts.append((sub_str, dominant_script(sub_str), cur_st, cur_st + len(sub_str)))
                        cur_sc = ch_sc
                        cur_buf = [ch]
                        cur_st = start + idx_ch
                if cur_buf:
                    sub_str = "".join(cur_buf)
                    sub_parts.append((sub_str, dominant_script(sub_str), cur_st, cur_st + len(sub_str)))
                new_segments.extend(sub_parts)
            else:
                new_segments.append((tok, script, start, end))
        return new_segments

    @staticmethod
    def segment(text: str) -> List[Tuple[str, str, int, int]]:
        if not text:
            return []
        entity_spans = []
        for m in URL_REGEX.finditer(text):
            entity_spans.append((m.start(), m.end(), 'URL'))
        for m in MENTION_REGEX.finditer(text):
            if not any(s <= m.start() < e for s, e, _ in entity_spans):
                entity_spans.append((m.start(), m.end(), 'MENTION'))
        entity_spans.sort(key=lambda x: x[0])

        if not entity_spans:
            return Tokenizer._segment_text_tokens(text, 0)

        segments = []
        last_end = 0
        for s_st, s_en, _ in entity_spans:
            if s_st > last_end:
                sub = text[last_end:s_st]
                sub_segs = Tokenizer._segment_text_tokens(sub, last_end)
                for tok, sc, st, en in sub_segs:
                    segments.append((tok, sc, last_end + st, last_end + en))
            ent_str = text[s_st:s_en]
            segments.append((ent_str, "ENTITY", s_st, s_en))
            last_end = s_en

        if last_end < len(text):
            sub = text[last_end:]
            sub_segs = Tokenizer._segment_text_tokens(sub, last_end)
            for tok, sc, st, en in sub_segs:
                segments.append((tok, sc, last_end + st, last_end + en))

        return segments

    @staticmethod
    def segment_text_with_offsets(text: str) -> List[Tuple[str, str, int, int]]:
        return Tokenizer.segment(text)


# ------------------------------------------------------------------------------
# 2. CANDIDATE DETECTOR: Global candidate discovery
# ------------------------------------------------------------------------------
class CandidateDetector:
    @staticmethod
    def detect(text: str, models: List[BaseLanguageModel], segments: List[Tuple[str, str, int, int]] = None) -> Set[str]:
        if not text or not text.strip():
            return {"en"}
        D: Set[str] = set()
        glotlid = next((e for e in models if isinstance(e, GlotLIDModel)), None)
        lingua = next((e for e in models if isinstance(e, LinguaModel)), None)
        fasttext = next((e for e in models if isinstance(e, FastTextModel)), None)

        if segments is None:
            segments = Tokenizer.segment(text)

        has_latin = False
        has_han = False
        has_kana = False
        has_arabic = False
        has_cyrillic = False
        has_devanagari = False
        has_bengali = False
        scripts_in_text: Set[str] = set()

        for ch in text:
            sc = get_script(ch)
            scripts_in_text.add(sc)
            if sc == "LATIN": has_latin = True
            elif sc == "HAN": has_han = True
            elif sc in ("HIRAGANA", "KATAKANA"): has_kana = True
            elif sc == "ARABIC": has_arabic = True
            elif sc == "CYRILLIC": has_cyrillic = True
            elif sc == "DEVANAGARI": has_devanagari = True
            elif sc == "BENGALI": has_bengali = True
            elif sc in SCRIPT_TO_DEFAULT_LANG:
                D.add(SCRIPT_TO_DEFAULT_LANG[sc])

        if has_kana:
            D.add("ja")
        if has_han:
            if not has_kana:
                D.add("zh")
            else:
                g_zh = glotlid.predict(text, ["zh", "ja"]).get("zh", 0.0) if glotlid else 0.0
                if g_zh >= 0.45:
                    D.add("zh")
                D.add("ja")
        if has_bengali: D.add("bn")

        if has_devanagari and glotlid:
            dev_runs = [seg[0] for seg in segments if seg[1] == "DEVANAGARI"]
            dev_text = " ".join(dev_runs)
            d_preds = glotlid.predict(dev_text or text, ["hi", "mr"])
            if d_preds:
                top_d, top_dp = max(d_preds.items(), key=lambda x: x[1])
                D.add(top_d)
                min_dp = 0.45 if top_dp >= 0.55 else 0.35
                for l, p in d_preds.items():
                    if l != top_d and p >= min_dp: D.add(l)
            else:
                D.add("hi")

        if has_arabic:
            has_urdu_chars = any(c in text for c in ['\u06D2', '\u0679', '\u0688', '\u0691', '\u06C1', '\u06BE', '\u06BA'])
            # Note: \u067E (pe), \u0686 (che), \u0698 (zhe), \u06AF (gaf) are shared between Persian and Urdu.
            has_persian_chars = any(c in text for c in ['\u067E', '\u0686', '\u0698', '\u06AF']) and not has_urdu_chars

            ar_runs = [seg[0] for seg in segments if seg[1] == "ARABIC"]
            ar_text = " ".join(ar_runs)
            a_preds = glotlid.predict(ar_text or text, ["ar", "ur", "fa"]) if glotlid else {}
            ft_preds = fasttext.predict(ar_text or text, ["ar", "ur", "fa"]) if fasttext else {}
            combined = {}
            for l in ["ar", "ur", "fa"]:
                combined[l] = 0.5 * a_preds.get(l, 0.0) + 0.5 * ft_preds.get(l, 0.0)

            if has_urdu_chars:
                D.add("ur")
            if has_persian_chars:
                D.add("fa")

            if combined:
                top_a, top_ap = max(combined.items(), key=lambda x: x[1])
                if has_urdu_chars:
                    D.add("ur")
                    if combined.get("ar", 0.0) >= 0.40:
                        D.add("ar")
                elif has_persian_chars and top_a == "fa":
                    D.add("fa")
                elif top_a == "ur" and top_ap >= 0.55:
                    D.add("ur")
                    if combined.get("ar", 0.0) >= 0.35:
                        D.add("ar")
                else:
                    D.add("ar")

                for l, p in combined.items():
                    if l == "fa" and not has_persian_chars:
                        continue
                    if l == "ur" and not has_urdu_chars and p < 0.45:
                        continue
                    if l == "ar" and has_urdu_chars and p < 0.45:
                        continue
                    if p >= 0.40 and (top_ap - p) < 0.20:
                        D.add(l)
            else:
                D.add("ur" if has_urdu_chars else ("fa" if has_persian_chars else "ar"))

            # Farsi sister suppression if Persian-exclusive letters absent
            if not has_persian_chars:
                D.discard("fa")
            arabic_family = {"ar", "ur", "fa"}
            if not (D & arabic_family):
                D.add("ar")
            if has_latin:
                D.add("en")

        if has_cyrillic:
            cyr_runs = [seg[0] for seg in segments if seg[1] == "CYRILLIC"]
            cyr_text = " ".join(cyr_runs)
            cyr_lower = cyr_text.lower()
            has_uk_chars = any(c in cyr_lower for c in ['і', 'ї', 'є', 'ґ'])
            # Russian exclusive vowels (not in Bulgarian or Ukrainian): ы, э, ё
            has_ru_chars = any(c in cyr_lower for c in ['ы', 'э', 'ё'])
            # Bulgarian uses ъ as a frequent vowel, but does not use Russian ы, э, ё or Ukrainian і, ї, є, ґ
            has_bg_chars = ('ъ' in cyr_lower and not has_ru_chars and not has_uk_chars)
            has_mn_chars = any(c in cyr_lower for c in ['ө', 'ү'])

            cyr_pool = ["ru", "bg", "uk", "be", "sr", "mk", "kk", "mn"]
            c_preds_g = glotlid.predict(cyr_text or text, cyr_pool) if glotlid else {}
            c_preds_ft = fasttext.predict(cyr_text or text, cyr_pool) if fasttext else {}

            if has_mn_chars: D.add("mn")
            if has_bg_chars: D.add("bg")
            if has_uk_chars: D.add("uk")
            if has_ru_chars: D.add("ru")

            # Statistical ensemble consensus across GlotLID and FastText
            combined_cyr: Dict[str, float] = {}
            for l, p in c_preds_g.items():
                combined_cyr[l] = combined_cyr.get(l, 0.0) + p * 0.5
            for l, p in c_preds_ft.items():
                combined_cyr[l] = combined_cyr.get(l, 0.0) + p * 0.5

            if combined_cyr:
                top_c, top_cp = max(combined_cyr.items(), key=lambda x: x[1])
                D.add(top_c)
                for l, p in combined_cyr.items():
                    if p >= 0.10:
                        if l == "bg" and (has_ru_chars or has_uk_chars):
                            continue
                        D.add(l)

            # Token-level statistical support for code-switched Cyrillic tokens
            if fasttext:
                for seg in segments:
                    if seg[1] == "CYRILLIC" and len(seg[0]) >= 3:
                        t_pred = fasttext.predict(seg[0], ["ru", "uk"])
                        if t_pred.get("ru", 0.0) >= 0.60:
                            D.add("ru")
                        if t_pred.get("uk", 0.0) >= 0.60:
                            D.add("uk")

            if not (D & {"ru", "uk", "bg", "mn", "be", "sr", "mk", "kk"}):
                D.add("ru")

        if has_latin:
            D.add("en")
            latin_runs = [seg[0] for seg in segments if seg[1] == "LATIN"]
            latin_text = " ".join(latin_runs)
            lt_lower = latin_text.lower()

            # ------------------------------------------------------------------
            # Latin-script unique-character map
            # Mirrors the exact same pattern used above for Arabic-script languages
            # (Urdu/Farsi detected by specific Unicode chars at lines 634-637).
            # Each character here is exclusive to its language by Unicode standard /
            # ISO 639 definition — not a heuristic, not a wordlist, no training data.
            # ------------------------------------------------------------------
            _CHAR_LANG = {
                # Turkish (ISO 639-1: tr)
                # ğ U+011F, Ğ U+011E — unique to Turkish orthography (1928 reform)
                # ş U+015F, Ş U+015E — unique to Turkish orthography
                # ı U+0131 (dotless i) — unique to Turkish
                # İ U+0130 (dotted I)  — unique to Turkish
                'ğ': 'tr', 'Ğ': 'tr',
                'ş': 'tr', 'Ş': 'tr',
                'ı': 'tr',
                'İ': 'tr',
                # German (ISO 639-1: de)
                # ß U+00DF (eszett) — exclusively German; Swiss Standard German
                # uses 'ss' instead, but ß itself appears nowhere else.
                'ß': 'de', 'ẞ': 'de',
                # ä U+00E4, Ä U+00C4 — does NOT appear in Turkish orthography
                # (Turkish uses 'a', never ä). Shared with Swedish/Finnish/Estonian
                # but not Turkish, so its presence strongly excludes Turkish.
                'ä': 'de', 'Ä': 'de',
                # ö U+00F6, Ö U+00D6 — Turkish DOES use ö/Ö so we do NOT add these.
                # ü U+00FC, Ü U+00DC — Turkish DOES use ü/Ü so we do NOT add these.
            }
            _langs_from_chars = {_lang for _ch, _lang in _CHAR_LANG.items()
                                  if _ch in latin_text}
            D.update(_langs_from_chars)

            # ------------------------------------------------------------------
            # Standard LID-confidence-based discovery (unchanged from baseline)
            # ------------------------------------------------------------------
            g_preds = {}
            l_preds = {}
            if glotlid and latin_text:
                g_preds = glotlid.predict(latin_text, None)
                sorted_g = sorted(g_preds.items(), key=lambda x: x[1], reverse=True)
                if sorted_g:
                    top_l, top_p = sorted_g[0]
                    D.add(top_l)
                    min_p = 0.35 if top_p >= 0.55 else 0.28
                    for l, p in sorted_g[1:4]:
                        if l in ("sl", "sk", "ro", "cs", "et", "sw", "tl", "ms", "hu", "ca", "zu", "af", "cy", "so", "nn"):
                            if p >= 0.50: D.add(l)
                        elif p >= min_p:
                            D.add(l)
            if lingua and latin_text:
                l_preds = lingua.predict(latin_text, None)
                sorted_l = sorted(l_preds.items(), key=lambda x: x[1], reverse=True)
                if sorted_l:
                    top_l, top_p = sorted_l[0]
                    top_g_p = sorted_g[0][1] if sorted_g else 0.0
                    if top_g_p >= 0.80:
                        if top_p >= 0.55 or top_l in D:
                            D.add(top_l)
                    elif top_g_p >= 0.60:
                        if top_p >= 0.45 or top_l in D:
                            D.add(top_l)
                    else:
                        if top_l in ("sl", "sk", "ro", "cs", "et", "sw", "tl", "ms", "hu", "ca", "zu", "af", "cy", "so", "nn"):
                            if top_p >= 0.50: D.add(top_l)
                        else:
                            D.add(top_l)
                        min_p = 0.35 if top_p >= 0.55 else 0.28
                        for l, p in sorted_l[1:3]:
                            if l in ("sl", "sk", "ro", "cs", "et", "sw", "tl", "ms", "hu", "ca", "zu", "af", "cy", "so", "nn"):
                                if p >= 0.50: D.add(l)
                            elif p >= min_p:
                                D.add(l)
            if fasttext and latin_text:
                f_preds = fasttext.predict(latin_text, None)
                if sorted_l and f_preds:
                    top_ft, ft_conf, _ = top_label(f_preds)
                    top_l, l_conf = sorted_l[0]
                    if top_ft == top_l and top_ft in SUPPORTED_LANGS:
                        if ft_conf >= 0.35 and l_conf >= 0.18:
                            D.add(top_ft)
            clean_latin_runs = [seg[0] for seg in segments if seg[1] == "LATIN"]
            chunk_discovered = set()
            if len(clean_latin_runs) >= 4:
                chunk_indices = list(range(0, len(clean_latin_runs) - 3, 3))
                tail_idx = max(0, len(clean_latin_runs) - 4)
                if tail_idx not in chunk_indices:
                    chunk_indices.append(tail_idx)
                for i in chunk_indices:
                    chunk = " ".join(clean_latin_runs[i:i+4])
                    ft_preds = fasttext.predict(chunk, None) if fasttext else {}
                    top_ft, ft_p, _ = top_label(ft_preds) if ft_preds else ("", 0.0, 0.0)
                    g_chunk = glotlid.predict(chunk, None) if glotlid else {}
                    l_chunk = lingua.predict(chunk, None) if lingua else {}
                    for l, gp in sorted(g_chunk.items(), key=lambda x: x[1], reverse=True)[:2]:
                        lp = l_chunk.get(l, 0.0)
                        fp = ft_preds.get(l, 0.0)
                        min_req = 0.45 if l in ("ca", "zu", "sl", "af", "cy", "pt") else 0.38
                        if (gp >= min_req and lp >= 0.20) or (gp >= 0.80 and fp >= 0.80 and lp >= 0.15):
                            D.add(l)
                            chunk_discovered.add(l)
                        elif gp >= 0.85 and (lp >= 0.15 or (fp >= 0.25 and lp >= 0.10)):
                            D.add(l)
                            chunk_discovered.add(l)
                        elif gp >= 0.98 and lp >= 0.10 and l not in ("ca", "zu", "sl", "af", "cy", "so"):
                            D.add(l)
                            chunk_discovered.add(l)
                    for l, lp in sorted(l_chunk.items(), key=lambda x: x[1], reverse=True)[:2]:
                        gp = g_chunk.get(l, 0.0)
                        min_req = 0.48 if l in ("ca", "zu", "sl", "af", "cy", "pt") else 0.42
                        if lp >= min_req and gp >= 0.20:
                            D.add(l)
                            chunk_discovered.add(l)
                    # FastText + GlotLID consensus for short Germanic/Romance chunks
                    if top_ft and top_ft in SUPPORTED_LANGS:
                        gp_ft = g_chunk.get(top_ft, 0.0)
                        if ft_p >= 0.60 and gp_ft >= 0.30 and top_ft not in ("ca", "zu", "sl", "af", "cy", "so"):
                            D.add(top_ft)
                            chunk_discovered.add(top_ft)

            # ------------------------------------------------------------------
            # MaskLID-inspired Iterative Residual Discovery (Consensus-Verified)
            # ------------------------------------------------------------------
            if glotlid and len(clean_latin_runs) >= 4:
                top_dom, top_dom_p = (sorted_g[0] if sorted_g else ("", 0.0))
                if top_dom_p >= 0.65:
                    residual_tokens = []
                    for tok in clean_latin_runs:
                        if len(tok) <= 2:
                            continue
                        fp = fasttext.predict(tok, None) if fasttext else {}
                        top_f, fp_conf, _ = top_label(fp) if fp else (None, 0.0, 0.0)
                        if top_f == top_dom and fp_conf >= 0.65:
                            continue
                        residual_tokens.append(tok)

                    if len(residual_tokens) >= 3:
                        res_str = " ".join(residual_tokens)
                        res_g = glotlid.predict(res_str, None) if glotlid else {}
                        res_l = lingua.predict(res_str, None) if lingua else {}
                        res_f = fasttext.predict(res_str, None) if fasttext else {}

                        for l, gp in sorted(res_g.items(), key=lambda x: x[1], reverse=True)[:2]:
                            if l in SUPPORTED_LANGS and l != top_dom:
                                lp = res_l.get(l, 0.0)
                                fp = res_f.get(l, 0.0)
                                if (gp >= 0.40 and lp >= 0.25) or (gp >= 0.40 and fp >= 0.35) or gp >= 0.85:
                                    if l not in ("ca", "zu", "sl", "af", "cy", "pt", "so", "la", "eo"):
                                        D.add(l)

            # ------------------------------------------------------------------
            # Clustered Minority-Switch Residual Discovery (Trace-Verified Consensus)
            # ------------------------------------------------------------------
            if glotlid and len(clean_latin_runs) >= 2:
                top_dom, _ = (sorted_g[0] if sorted_g else ("", 0.0))
                cand_groups = defaultdict(list)
                for tok in clean_latin_runs:
                    if len(tok) < 4:
                        continue
                    fp = fasttext.predict(tok, None) if fasttext else {}
                    top_f, fp_conf, _ = top_label(fp) if fp else (None, 0.0, 0.0)
                    if top_f == top_dom and fp_conf >= 0.60:
                        continue
                    if top_f and top_f != top_dom and top_f in SUPPORTED_LANGS:
                        cand_groups[top_f].append((tok, fp_conf))

                noisy_residual_langs = {
                    "ca", "zu", "sl", "af", "cy", "pt", "so", "la", "eo",
                    "nn", "da", "sv", "nb", "no", "eu", "sk", "et", "hr",
                    "lt", "lv", "ro", "cs", "fi", "hu", "pl", "nl", "it", "sw"
                }

                for cand_l, tok_tuples in cand_groups.items():
                    if cand_l in noisy_residual_langs or cand_l in D:
                        continue
                    toks = [t[0] for t in tok_tuples]
                    max_f_conf = max(t[1] for t in tok_tuples)

                    sent_g_trace = g_preds.get(cand_l, 0.0)
                    sent_l_trace = l_preds.get(cand_l, 0.0)
                    if sent_g_trace < 0.015 and sent_l_trace < 0.015:
                        continue

                    clustered_str = " ".join(toks)
                    cg_preds = glotlid.predict(clustered_str, None) if glotlid else {}
                    gp = cg_preds.get(cand_l, 0.0)

                    # Multiple content tokens (len >= 2) agreeing on candidate
                    if len(toks) >= 2:
                        if gp >= 0.35:
                            cl_preds = lingua.predict(clustered_str, None) if lingua else {}
                            lp = cl_preds.get(cand_l, 0.0)
                            if lp >= 0.20 or gp >= 0.70 or max_f_conf >= 0.75:
                                D.add(cand_l)
                    # Single unambiguous content word (len >= 5) with high multi-model consensus
                    elif len(toks) == 1 and len(toks[0]) >= 5:
                        if max_f_conf >= 0.80 and gp >= 0.80:
                            D.add(cand_l)

            # Multi-model token consensus candidate recovery for intra-script German/Turkish
            # When a content word (len >= 4) receives decisive multi-model agreement across FastText,
            # GlotLID, and Lingua, recover the candidate language even if sentence-level LID was diluted.
            missing_intra = {"de", "tr"} - D
            if missing_intra and len(clean_latin_runs) >= 1:
                for tok in clean_latin_runs:
                    if not ({"de", "tr"} - D):
                        break
                    if len(tok) < 4:
                        continue
                    fp = fasttext.predict(tok, None) if fasttext else {}
                    gp = glotlid.predict(tok, None) if glotlid else {}
                    lp = lingua.predict(tok, None) if lingua else {}
                    top_f, fc, _ = top_label(fp) if fp else ("", 0.0, 0.0)
                    top_g, gc, _ = top_label(gp) if gp else ("", 0.0, 0.0)
                    top_l, lc, _ = top_label(lp) if lp else ("", 0.0, 0.0)
                    for cand in ("de", "tr"):
                        if cand in D:
                            continue
                        votes = 0
                        if top_f == cand and fc >= 0.40:
                            votes += 1
                        if top_g == cand and gc >= 0.45:
                            votes += 1
                        if top_l == cand and lc >= 0.30:
                            votes += 1
                        # Germanic cluster consensus: FastText & GlotLID agree word is Germanic,
                        # and at least one model specifically identifies German 'de'
                        if cand == "de":
                            ger_cluster = {"de", "nl", "da", "sv", "no"}
                            if top_f in ger_cluster and top_g in ger_cluster:
                                if "de" in (top_f, top_g, top_l) or (lp and lp.get("de", 0.0) >= 0.15):
                                    votes = max(votes, 2)
                        if votes >= 2:
                            D.add(cand)

            # Sister language mutual suppression (Indonesian vs Malay)
            if "id" in D or "ms" in D:
                s_id_g = g_preds.get("id", 0.0)
                s_ms_g = g_preds.get("ms", 0.0)
                s_id_l = l_preds.get("id", 0.0)
                s_ms_l = l_preds.get("ms", 0.0)
                s_id_f = f_preds.get("id", 0.0) if f_preds else 0.0
                s_ms_f = f_preds.get("ms", 0.0) if f_preds else 0.0
                s_id_tot = s_id_g + s_id_l + s_id_f
                s_ms_tot = s_ms_g + s_ms_l + s_ms_f
                if "id" in D and "ms" in D:
                    if s_id_tot >= s_ms_tot:
                        D.discard("ms")
                    elif s_ms_g >= 0.70 and s_id_tot < 0.20 and "id" not in chunk_discovered:
                        D.discard("id")
                    else:
                        D.discard("ms")
                elif "ms" in D and "id" not in D:
                    if s_id_tot >= 0.25 or s_id_tot >= s_ms_tot:
                        D.add("id")
                        if s_id_tot >= s_ms_tot:
                            D.discard("ms")

            if "id" in D:
                if "de" in D and not any(c in lt_lower for c in 'äöüß'):
                    if g_preds.get("de", 0.0) < 0.10 and l_preds.get("de", 0.0) < 0.10:
                        D.discard("de")

            if "vi" in D and not any(c in lt_lower for c in 'ăâđêôơưàảãáạèẻẽéẹìỉĩíịòỏõóọùủũúụỳỷỹýỵ'):
                D.discard("vi")
            if "yo" in D:
                if not any(c in lt_lower for c in 'ẹọṣ'):
                    if "es" in D and g_preds.get("yo", 0.0) < 0.20:
                        D.discard("yo")
                    elif not any(c in lt_lower for c in 'àáèéìíòóùú'):
                        D.discard("yo")
            if "tr" in D and "az" in D:
                D.discard("az")
            if "tr" in D:
                s_en_g = g_preds.get("en", 0.0) if g_preds else 0.0
                s_en_l = l_preds.get("en", 0.0) if l_preds else 0.0
                en_is_real = (s_en_g >= 0.15 or s_en_l >= 0.15)
                if not en_is_real:
                    germanic_outliers = {"nl", "da", "sv", "no", "nn"} & D
                    if germanic_outliers:
                        D.add("de")
                        D.difference_update(germanic_outliers)

            # Disambiguate Turkish-German vs Turkish-English when both 'de' and 'en' compete with 'tr'
            if "tr" in D and "de" in D and "en" in D:
                has_de_markers = any(c in lt_lower for c in 'äß')
                s_de_g = g_preds.get("de", 0.0) if g_preds else 0.0
                s_de_l = l_preds.get("de", 0.0) if l_preds else 0.0
                s_de_f = f_preds.get("de", 0.0) if f_preds else 0.0
                de_is_real = has_de_markers or s_de_g >= 0.15 or s_de_l >= 0.15 or s_de_f >= 0.15

                s_en_g = g_preds.get("en", 0.0) if g_preds else 0.0
                s_en_l = l_preds.get("en", 0.0) if l_preds else 0.0
                s_en_f = f_preds.get("en", 0.0) if f_preds else 0.0
                en_is_real = (s_en_g >= 0.10 or s_en_l >= 0.10 or s_en_f >= 0.10)

                if de_is_real and not en_is_real:
                    D.discard("en")
                elif en_is_real and not de_is_real:
                    D.discard("de")
                elif not de_is_real and not en_is_real:
                    s_de_tot = s_de_g + s_de_l + s_de_f
                    s_en_tot = s_en_g + s_en_l + s_en_f
                    if s_en_tot >= s_de_tot:
                        D.discard("de")
                    else:
                        D.discard("en")
            if "hu" in D and not any(c in lt_lower for c in 'őűáéíóöúü'):
                if "en" in D or "es" in D or "tr" in D:
                    D.discard("hu")
            if "eo" in D and not any(c in lt_lower for c in 'ĉĝĥĵŝŭ'):
                D.discard("eo")
            # Dutch suppression: only if NL model trace is weak — 'ij' alone is not
            # a reliable enough signal; real Dutch uses common words like 'dus', 'maar', 'ik'.
            if "nl" in D and "es" in D and not any(c in lt_lower for c in 'ij'):
                s_nl = g_preds.get("nl", 0.0)
                s_es = g_preds.get("es", 0.0)
                # Only suppress NL if ES is very dominant and NL has almost no model support
                if s_es >= 0.50 and s_nl < 0.10:
                    D.discard("nl")

            # Portuguese-exclusive diacritics: ã, õ, ç, ê, â (á is shared with ES/IT).
            # Only suppress pt when no PT-specific chars AND ES is strongly dominant.
            # A lenient threshold preserves pt in genuine es+pt bilingual text.
            if "pt" in D and "es" in D:
                has_pt_exclusive = any(c in lt_lower for c in 'ãõçêâ')
                has_es_markers = any(c in lt_lower for c in 'áéíóúñ¿¡')
                s_es = g_preds.get("es", 0.0)
                s_pt = g_preds.get("pt", 0.0)
                if has_es_markers and not has_pt_exclusive and s_es >= 0.45 and s_pt < 0.20:
                    D.discard("pt")
                elif not has_pt_exclusive and s_es >= 0.60 and s_pt < 0.15:
                    D.discard("pt")

            # Italian in predominantly Spanish text (preserve if verified in chunk)
            if "it" in D and "es" in D and not any(c in lt_lower for c in 'àèìòù'):
                if "it" not in chunk_discovered:
                    s_es = g_preds.get("es", 0.0)
                    s_it = g_preds.get("it", 0.0)
                    if s_es >= 0.30 and (s_es >= s_it or s_it < 0.15):
                        D.discard("it")

            # Intrusive noise languages when Spanish is dominant
            if "es" in D and g_preds.get("es", 0.0) >= 0.35:
                for noise in ("sl", "so", "fi", "nl", "la"):
                    if noise in D and noise not in chunk_discovered:
                        D.discard(noise)
                    if noise in D and noise not in chunk_discovered:
                        D.discard(noise)
            if "ms" in D and "es" in D:
                D.discard("ms")
            if "id" in D and "es" in D:
                D.discard("id")

            if "ca" in D:
                if not any(c in lt_lower for c in ('l·l', '·', 'ny', 'ç')):
                    if "es" in D or "fr" in D or "pt" in D:
                        D.discard("ca")

            # es/pt mutual suppression: sentence-level model scores are unreliable
            # in genuine bilingual es+pt text because each language only appears in
            # one clause. Only suppress if the winner is EXTREMELY dominant (≥0.70)
            # and the loser has near-zero signal AND was not discovered in a localized chunk.
            if "es" in D and "pt" in D and "it" not in D:
                s_es = g_preds.get("es", 0.0)
                s_pt = g_preds.get("pt", 0.0)
                if s_es >= 0.70 and s_pt < 0.10 and "pt" not in chunk_discovered:
                    D.discard("pt")
                elif s_pt >= 0.70 and s_es < 0.10 and "es" not in chunk_discovered:
                    D.discard("es")

            # Portuguese without PT-exclusive diacritics when spurious:
            # If PT has NO chunks and NO Portuguese-exclusive diacritics (ã, õ):
            if "pt" in D and "pt" not in chunk_discovered and not any(c in lt_lower for c in 'ãõ'):
                if "fr" in D:
                    D.discard("pt")
                elif "es" in D and g_preds.get("pt", 0.0) < 0.20:
                    D.discard("pt")

            if "pt" in D and "en" in D and "es" not in D and "it" not in D:
                s_en = g_preds.get("en", 0.0)
                s_pt = g_preds.get("pt", 0.0)
                if s_en >= 0.40 and s_pt <= 0.30:
                    D.discard("pt")

            if "cy" in D and "en" in D:
                if not any(c in lt_lower for c in ('dd', 'ff', 'll', 'rh')):
                    D.discard("cy")

            if "sl" in D and not any(c in lt_lower for c in 'čšž'):
                D.discard("sl")

            if "sw" in D and "sw" not in chunk_discovered:
                if not (g_preds.get("sw", 0.0) >= 0.60 or (g_preds.get("sw", 0.0) >= 0.45 and l_preds.get("sw", 0.0) >= 0.35)):
                    D.discard("sw")

            if "sk" in D and not any(c in lt_lower for c in 'ôŕĺľťďň'):
                D.discard("sk")

            if "ro" in D and not any(c in lt_lower for c in 'ăâîșțşţ'):
                D.discard("ro")

            if "cs" in D and not any(c in lt_lower for c in 'řěů'):
                D.discard("cs")

            if "et" in D and not any(c in lt_lower for c in 'õäöü'):
                if "et" not in chunk_discovered and not (g_preds.get("et", 0.0) >= 0.60 or (g_preds.get("et", 0.0) >= 0.45 and l_preds.get("et", 0.0) >= 0.35)):
                    D.discard("et")

            if "nn" in D and "nn" not in chunk_discovered:
                if not (g_preds.get("nn", 0.0) >= 0.60 or (g_preds.get("nn", 0.0) >= 0.45 and l_preds.get("nn", 0.0) >= 0.35)):
                    D.discard("nn")

            if "tl" in D and "tl" not in chunk_discovered:
                if not (g_preds.get("tl", 0.0) >= 0.60 or (g_preds.get("tl", 0.0) >= 0.45 and l_preds.get("tl", 0.0) >= 0.35)):
                    D.discard("tl")

            if "ms" in D:
                if "id" in D or ("ms" not in chunk_discovered and not (g_preds.get("ms", 0.0) >= 0.70 or (g_preds.get("ms", 0.0) >= 0.55 and l_preds.get("ms", 0.0) >= 0.40))):
                    D.discard("ms")

            if "hu" in D and not any(c in lt_lower for c in 'őű'):
                if "hu" not in chunk_discovered and not (g_preds.get("hu", 0.0) >= 0.70 or (g_preds.get("hu", 0.0) >= 0.55 and l_preds.get("hu", 0.0) >= 0.40)):
                    D.discard("hu")

            if "zu" in D and "en" in D:
                D.discard("zu")

            # Han-script Latin disambiguation: In Chinese Han text with Latin, natural code-switching
            # is overwhelmingly Mandarin-English (Chinglish). Suppress spurious regional languages that enter
            # due to cognates in short English words (e.g. 'doorman' -> nl, 'den' -> de, 'pizza' -> it,
            # 'house' -> hi, 'sheet' -> hi, 'share' -> sv).
            # Genuine multi-lingual code-switching (e.g. zh+de or zh+fr) is verified by localized chunks or diacritics.
            if has_han and not has_kana and "en" in D:
                for extraneous in list(D):
                    if extraneous in ("zh", "en"):
                        continue
                    # Non-Latin script preservation: never prune languages whose non-Latin script is genuinely present in the text
                    non_latin_scripts = [sc for sc, langs in SCRIPT_TO_LANGUAGES.items() if sc != "LATIN" and extraneous in langs]
                    if any(sc in scripts_in_text for sc in non_latin_scripts):
                        continue
                    if extraneous == "es" and any(c in lt_lower for c in 'áéíóúñ¿¡'):
                        continue
                    if extraneous == "fr" and any(c in lt_lower for c in 'àâçèéêëîïôùûüÿœæ'):
                        continue
                    if extraneous == "it" and any(c in lt_lower for c in 'àèéìòù'):
                        continue
                    if extraneous == "pt" and any(c in lt_lower for c in 'ãõçáéíóúâêôà'):
                        continue
                    if extraneous == "de" and any(c in lt_lower for c in 'äöüß'):
                        continue
                    if extraneous not in chunk_discovered:
                        D.discard(extraneous)

        return (D & SUPPORTED_LANGS) or {"en"}


# ------------------------------------------------------------------------------
# 3. TOKEN CLASSIFIER: Token-level classification & local window context
# ------------------------------------------------------------------------------
class TokenClassifier:
    @staticmethod
    def classify_tokens(
        segments: List[Tuple[str, str, int, int]],
        candidate_langs: Set[str],
        models: List[BaseLanguageModel],
        text: str = "",
        tiebreaker_model: Optional[BaseLanguageModel] = None
    ) -> List[List[ModelPrediction]]:
        clause_has_kana = []
        for i, (tok_str, script, start_idx, end_idx) in enumerate(segments):
            c_start = i
            while c_start > 0:
                gap = text[segments[c_start - 1][3]:segments[c_start][2]] if text else ""
                if any(p in gap for p in CLAUSE_BREAKS): break
                c_start -= 1
            c_end = i + 1
            while c_end < len(segments):
                gap = text[segments[c_end - 1][3]:segments[c_end][2]] if text else ""
                if any(p in gap for p in CLAUSE_BREAKS): break
                c_end += 1
            clause_has_kana.append(any(segments[k][1] in ("HIRAGANA", "KATAKANA") for k in range(c_start, c_end)))

        token_predictions: List[List[ModelPrediction]] = []
        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            if script == "ENTITY":
                token_predictions.append([])
                continue

            if script in SINGLETON_SCRIPTS:
                det_lang = SINGLETON_SCRIPTS[script]
                pred = ModelPrediction(det_lang, 1.0, 1.0, [(det_lang, 1.0)], "DeterministicScriptPrior", {det_lang: 1.0}, {det_lang: 1.0})
                token_predictions.append([pred])
                continue

            preds: List[ModelPrediction] = []
            clean_tok = token_str.strip('.,!?;:"\'()[]{}–') or token_str
            has_elong = bool(re.search(r'([a-zA-Z])\1{2,}', clean_tok))
            de_elong_1 = re.sub(r'([a-zA-Z])\1{2,}', r'\1', clean_tok)
            de_elong_2 = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', clean_tok)
            low_tok = clean_tok.lower()
            low_elong1 = de_elong_1.lower()
            low_elong2 = de_elong_2.lower()

            if clause_has_kana[idx] and script == "HAN":
                preds.append(ModelPrediction("ja", 0.99, 0.99, [("ja", 0.99)], "JapaneseKanjiTopology", {"ja": 0.99}, {"ja": 0.99}))
                token_predictions.append(preds)
                continue

            token_allowed = candidate_langs & SCRIPT_TO_LANGUAGES.get(script, candidate_langs)
            if not token_allowed:
                token_allowed = SCRIPT_TO_LANGUAGES.get(script, candidate_langs)

            # Clause-bounded 3-token window context string
            w_start = idx
            if idx > 0 and segments[idx - 1][1] == script:
                gap_l = text[segments[idx - 1][3]:segments[idx][2]] if text else ""
                if not any(p in gap_l for p in CLAUSE_BREAKS):
                    w_start = idx - 1
            w_end = idx + 1
            if idx + 1 < len(segments) and segments[idx + 1][1] == script:
                gap_r = text[segments[idx][3]:segments[idx + 1][2]] if text else ""
                if not any(p in gap_r for p in CLAUSE_BREAKS):
                    w_end = idx + 2
            window_toks = [segments[w_i][0] for w_i in range(w_start, w_end) if segments[w_i][1] == script]
            window_str = " ".join(window_toks) if len(window_toks) > 1 else clean_tok

            for model in models:
                if model.supports_token(clean_tok, script, token_allowed):
                    raw_dist, res_dist = {}, {}
                    if has_elong:
                        _, d1 = model.evaluate(de_elong_1, token_allowed)
                        _, d2 = model.evaluate(de_elong_2, token_allowed)
                        m1 = top_label(d1)[2] if d1 else 0
                        m2 = top_label(d2)[2] if d2 else 0
                        if m1 >= m2 and m1 >= 0.20:
                            res_dist, raw_dist = d1, d1
                        elif m2 >= 0.20:
                            res_dist, raw_dist = d2, d2

                    if not res_dist:
                        raw_dist, res_dist = model.evaluate(clean_tok, token_allowed)

                    raw_conf = raw_dist.get(top_label(res_dist)[0], 0.0) if raw_dist and res_dist else 0.0
                    res_margin = top_label(res_dist)[2] if res_dist else 0.0
                    is_intra_tr_de = (token_allowed is not None and "de" in token_allowed and "tr" in token_allowed)
                    if not res_dist or res_margin < 0.20 or (is_intra_tr_de and len(clean_tok) <= 3 and raw_conf < 0.25):
                        if window_str != clean_tok:
                            _, win_dist = model.evaluate(window_str, token_allowed)
                            if win_dist:
                                res_dist, raw_dist = win_dist, win_dist

                    if res_dist:
                        lab, conf, margin = top_label(res_dist)
                        ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                        preds.append(ModelPrediction(lab, conf, margin, ranked, model.name, raw_dist, res_dist))

            # Statistical model tiebreaker for intra-script German/Turkish disambiguation
            if tiebreaker_model and "de" in candidate_langs and "tr" in candidate_langs and script == "LATIN" and len(clean_tok) >= 2:
                p_models = {p.model.lower(): p for p in preds}
                ft_p = p_models.get("fasttext")
                lg_p = p_models.get("lingua")
                if ft_p and lg_p and ft_p.label != lg_p.label:
                    if {ft_p.label, lg_p.label} & {"de", "tr"}:
                        raw_dist, res_dist = tiebreaker_model.evaluate(clean_tok, candidate_langs)
                        if (not res_dist or top_label(res_dist)[2] < 0.20) and window_str != clean_tok:
                            _, win_dist = tiebreaker_model.evaluate(window_str, candidate_langs)
                            if win_dist:
                                res_dist, raw_dist = win_dist, win_dist
                        if res_dist:
                            lab, conf, margin = top_label(res_dist)
                            ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                            preds.append(ModelPrediction(lab, conf, margin, ranked, tiebreaker_model.name, raw_dist, res_dist))

            token_predictions.append(preds)
        return token_predictions


# ------------------------------------------------------------------------------
# 4. DECISION MAKER: Disagreement resolution & context checks
# ------------------------------------------------------------------------------
class PredictionAnalyzer:
    @staticmethod
    def analyze_and_validate(predictions, token_idx, scripts, token_str, allowed_langs=None):
        current_script = scripts[token_idx] if 0 <= token_idx < len(scripts) else "OTHER"
        prev_script = scripts[token_idx - 1] if token_idx > 0 else current_script
        next_script = scripts[token_idx + 1] if token_idx < len(scripts) - 1 else current_script
        script_changed = (
            (prev_script != current_script and prev_script != "OTHER" and current_script != "OTHER")
            or (next_script != current_script and next_script != "OTHER" and current_script != "OTHER")
        )
        raw_valid_preds = [p for p in predictions if p.label and 0.0 <= p.confidence <= 1.0 and p.margin >= 0.0]
        labels = {p.label for p in raw_valid_preds}
        models_disagree = len(labels) > 1
        is_switch_point = script_changed or models_disagree
        needs_arbitration = is_switch_point or len(raw_valid_preds) == 0

        boundary_ev = BoundaryEvidence(script_changed, models_disagree, is_switch_point, needs_arbitration)
        allowed_set = set(allowed_langs) if allowed_langs is not None else None
        valid_preds = [p for p in predictions if p.label and 0.0 <= p.confidence <= 1.0 and p.margin >= 0.0 and (not allowed_set or p.label in allowed_set)]
        label_counts = Counter(p.label for p in valid_preds)

        evidences = [
            PredictionEvidence(p.model, p, p.margin, p.confidence, boundary_ev, label_counts[p.label], current_script, token_str, p.ranked_candidates)
            for p in valid_preds
        ]
        return boundary_ev, evidences


class ContextChecker:
    @staticmethod
    def should_trigger(token_str, consensus_ev, boundary_ev, evidences, context_everywhere=False):
        if not token_str or not any(c.isalpha() for c in token_str): return False
        if context_everywhere: return True
        if boundary_ev.needs_arbitration: return True
        if any(c in INTERNAL_PUNCTUATION for c in token_str): return True
        if evidences:
            best = PredictionMerger.select_strongest(evidences)
            if best.script != 'LATIN':
                if len(token_str) < 2:
                    return False
                if best.margin <= 0.25 or len(token_str) <= 3:
                    return True
                return False
            # LATIN script: protect confident 2-3 char function words from being swallowed
            if len(token_str) == 1 or best.margin <= 0.25:
                return True
            if len(token_str) <= 3 and (boundary_ev.needs_arbitration or best.margin < 0.40):
                return True
        return False

    @staticmethod
    def analyze(token_idx, segments, candidate_langs, models, boundary_ev, text="", token_predictions=None):
        if not segments or not (0 <= token_idx < len(segments)): return []
        token_str, script, _, _ = segments[token_idx]
        start_w = token_idx
        while start_w > 0 and segments[start_w - 1][1] == script and (token_idx - start_w) < 2:
            gap = text[segments[start_w - 1][3]:segments[start_w][2]] if text else ""
            if any(p in gap for p in CLAUSE_BREAKS): break
            start_w -= 1
        end_w = token_idx + 1
        while end_w < len(segments) and segments[end_w][1] == script and (end_w - token_idx) <= 2:
            gap = text[segments[end_w - 1][3]:segments[end_w][2]] if text else ""
            if any(p in gap for p in CLAUSE_BREAKS): break
            if len(segments[end_w][0]) == 1: break
            end_w += 1

        local_evidences: List[PredictionEvidence] = []
        left_labs, right_labs = set(), set()
        def evaluate_phrase(phrase_str, prefix, lab_set=None):
            for model in models:
                if model.supports_token(token_str, script, candidate_langs):
                    raw_dist, res_dist = model.evaluate(phrase_str, candidate_langs)
                    if res_dist:
                        lab, conf, margin = top_label(res_dist)
                        if lab_set is not None: lab_set.add(lab)
                        ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                        m_name = f"LocalContext{prefix}({model.name})"
                        pred = ModelPrediction(lab, conf, margin, ranked, m_name, raw_dist, res_dist)
                        local_evidences.append(PredictionEvidence(m_name, pred, margin, conf, boundary_ev, 1, script, token_str, ranked))

        if end_w > token_idx + 1: evaluate_phrase(" ".join(segments[i][0] for i in range(token_idx, end_w)), "Right", right_labs)
        if start_w < token_idx: evaluate_phrase(" ".join(segments[i][0] for i in range(start_w, token_idx + 1)), "Left", left_labs)

        should_combine = (start_w < token_idx and end_w > token_idx + 1)
        if left_labs and right_labs and not (left_labs & right_labs):
            should_combine = False

        if should_combine:
            evaluate_phrase(" ".join(segments[i][0] for i in range(start_w, end_w)), "Combined")

        for e in local_evidences:
            agreeing_models = {
                other.model.split('(')[-1].rstrip(')')
                for other in local_evidences
                if other.prediction.label == e.prediction.label
            }
            e.agreement_count = len(agreeing_models)
        return local_evidences


class PredictionMerger:
    @staticmethod
    def is_stronger(ev1: PredictionEvidence, ev2: PredictionEvidence) -> bool:
        if ev1.agreement_count != ev2.agreement_count:
            return ev1.agreement_count > ev2.agreement_count
        tok_len = len(ev1.token.strip()) if ev1.token else 5
        # -- Lingua preference for short/medium tokens (Step 1: extend 4→6) --------
        # Turkish informal text frequently lacks diacritics (hic=hiç, cok=çok,
        # artik=artık, olsun, bende, sende). Without diacritics FastText's
        # restricted {tr,de} distribution normalizes residual mass to de=1.000
        # even though unconstrained FastText would choose English or another lang.
        # Lingua is NOT fooled and correctly identifies these as Turkish.
        # Extending the threshold from 4→6 covers: olsun(5), bende(5), sende(5),
        # artik(5), yine(4), hadi(4), var(3), hep(3), hic(3).
        if tok_len <= 6:
            m1_lingua = "lingua" in ev1.model.lower() and "localcontext" not in ev1.model.lower()
            m2_lingua = "lingua" in ev2.model.lower() and "localcontext" not in ev2.model.lower()
            if m1_lingua and not m2_lingua and ev1.margin >= 0.20:
                return True
            if m2_lingua and not m1_lingua and ev2.margin >= 0.20:
                return False
        # Spanish-English, Indonesian-English, and Turkish-English disambiguation on short tokens:
        # Protect direct Lingua native observation from LocalContext/FastText English override
        l1 = ev1.prediction.label if ev1.prediction else None
        l2 = ev2.prediction.label if ev2.prediction else None
        is_es_en_pair = (l1 in {"es", "en"} and l2 in {"es", "en"})
        if is_es_en_pair and tok_len <= 5:
            m1_lingua_es = "lingua" in ev1.model.lower() and "localcontext" not in ev1.model.lower() and l1 == "es"
            m2_lingua_es = "lingua" in ev2.model.lower() and "localcontext" not in ev2.model.lower() and l2 == "es"
            if m1_lingua_es and not m2_lingua_es and ev1.margin >= 0.25:
                return True
            if m2_lingua_es and not m1_lingua_es and ev2.margin >= 0.25:
                return False
        is_id_en_pair = (l1 in {"id", "en"} and l2 in {"id", "en"})
        if is_id_en_pair and tok_len <= 5:
            m1_lingua_id = "lingua" in ev1.model.lower() and "localcontext" not in ev1.model.lower() and l1 == "id"
            m2_lingua_id = "lingua" in ev2.model.lower() and "localcontext" not in ev2.model.lower() and l2 == "id"
            if m1_lingua_id and not m2_lingua_id and ev1.margin >= 0.25:
                return True
            if m2_lingua_id and not m1_lingua_id and ev2.margin >= 0.25:
                return False
        is_tr_en_pair = (l1 in {"tr", "en"} and l2 in {"tr", "en"})
        if is_tr_en_pair and tok_len <= 7:
            m1_lingua_tr = "lingua" in ev1.model.lower() and "localcontext" not in ev1.model.lower() and l1 == "tr"
            m2_lingua_tr = "lingua" in ev2.model.lower() and "localcontext" not in ev2.model.lower() and l2 == "tr"
            if m1_lingua_tr and not m2_lingua_tr and ev1.margin >= 0.25:
                return True
            if m2_lingua_tr and not m1_lingua_tr and ev2.margin >= 0.25:
                return False
        # -- Protect strong Lingua single-token from LocalContext window override ---
        # (Step 2) In Turkish-German sentences, LocalContext evidence items from a
        # 3-token window of German tokens pull surrounding Turkish tokens toward
        # German. When a single Lingua prediction is very confident (margin ≥ 0.75)
        # and the competing evidence is purely a LocalContext window artifact,
        # Lingua's direct token observation should win regardless of token length.
        if tok_len <= 8:
            ev1_is_local = "LocalContext" in ev1.model
            ev2_is_local = "LocalContext" in ev2.model
            ev1_is_lingua = "Lingua" in ev1.model and not ev1_is_local
            ev2_is_lingua = "Lingua" in ev2.model and not ev2_is_local
            # ev1 is a strong Lingua direct observation, ev2 is window context → ev1 wins
            if ev1_is_lingua and ev2_is_local and ev1.margin >= 0.75:
                return True
            # ev2 is a strong Lingua direct observation, ev1 is window context → ev2 wins
            if ev2_is_lingua and ev1_is_local and ev2.margin >= 0.75:
                return False
        if ev1.margin != ev2.margin:
            return ev1.margin > ev2.margin
        return ev1.confidence > ev2.confidence

    @staticmethod
    def select_strongest(evidences: List[PredictionEvidence]) -> PredictionEvidence:
        best = evidences[0]
        for ev in evidences[1:]:
            if PredictionMerger.is_stronger(ev, best): best = ev
        return best

    @staticmethod
    def fuse_consensus(evidences: List[PredictionEvidence], boundary_ev: BoundaryEvidence):
        if not evidences: return None, []
        groups = defaultdict(list)
        for ev in evidences: groups[ev.prediction.label].append(ev)
        agreed = [evs for evs in groups.values() if len(evs) >= 2]
        if not agreed: return None, evidences
        agreed_evs = agreed[0]
        lab = agreed_evs[0].prediction.label
        other = [ev for ev in evidences if ev.prediction.label != lab]
        avg_m = sum(e.margin for e in agreed_evs) / len(agreed_evs)
        avg_c = sum(e.confidence for e in agreed_evs) / len(agreed_evs)
        m_name = "+".join(e.model for e in agreed_evs)
        pred = ModelPrediction(lab, avg_c, avg_m, agreed_evs[0].prediction.ranked_candidates, m_name, agreed_evs[0].prediction.raw_dist, agreed_evs[0].prediction.res_dist)
        return PredictionEvidence(m_name, pred, avg_m, avg_c, boundary_ev, len(agreed_evs), agreed_evs[0].script, agreed_evs[0].token, agreed_evs[0].raw_candidates), other


class DecisionEngine:
    @staticmethod
    def arbitrate(evidences, token_idx, segments, boundary_ev, local_evidences=None):
        token_str, script, _, _ = segments[token_idx] if 0 <= token_idx < len(segments) else ("", "OTHER", 0, 0)
        
        # Enforce deterministic routing for singleton scripts
        if script in SINGLETON_SCRIPTS:
            det_lang = SINGLETON_SCRIPTS[script]
            return TokenDecision.create_with_trace(
                det_lang, "DeterministicScriptPrior",
                f"Deterministic script prior for {script}.",
                [("DeterministicScriptPrior", det_lang)],
                {det_lang: 1.0}, token_str,
                {"DeterministicScriptPrior": det_lang},
                DecisionStage.DETERMINISTIC_SCRIPT
            )

        all_ev = list(evidences) + (local_evidences or [])
        if not all_ev:
            default_lang = SCRIPT_TO_DEFAULT_LANG.get(script, "en")
            return TokenDecision.create_with_trace(default_lang, "DefaultScriptPrior", f"Defaulted to {default_lang}.", [], {default_lang: 1.0}, token_str, {}, DecisionStage.DETERMINISTIC_SCRIPT)

        competing = [(ev.model, ev.prediction.label) for ev in all_ev]
        m_preds = {ev.model: ev.prediction.label for ev in all_ev}

        # Length-adaptive consensus distribution pooling across models (giving higher weight to Lingua on short tokens <= 4 chars)
        merged_dist = {}
        target_evs = [ev for ev in all_ev if ev.prediction and ev.prediction.res_dist]
        if target_evs:
            tok_len = len(token_str.strip())
            total_w = 0.0
            ev_weights = []
            for ev in target_evs:
                m_name = ev.model.lower()
                if "lingua" in m_name:
                    w = 0.65 if tok_len <= 3 else (0.58 if tok_len == 4 else 0.50)
                elif "fasttext" in m_name:
                    w = 0.35 if tok_len <= 3 else (0.42 if tok_len == 4 else 0.50)
                else:
                    w = 0.50
                ev_weights.append(w)
                total_w += w

            for ev, w in zip(target_evs, ev_weights):
                norm_w = w / total_w
                for l, p in ev.prediction.res_dist.items():
                    merged_dist[l] = merged_dist.get(l, 0.0) + p * norm_w

        if not boundary_ev.needs_arbitration and not local_evidences:
            best_ev = PredictionMerger.select_strongest(evidences)
            stage = DecisionStage.UNANIMOUS if len(evidences) >= 2 or best_ev.agreement_count >= 2 else DecisionStage.EVIDENCE_COMPARISON
            return TokenDecision.create_with_trace(best_ev.prediction.label, best_ev.model, f"Selected {best_ev.prediction.label}.", competing, merged_dist or best_ev.prediction.res_dist, token_str, m_preds, stage)

        consensus_ev, dissent_evs = PredictionMerger.fuse_consensus(evidences, boundary_ev)
        if consensus_ev is not None:
            agreed_lab = consensus_ev.prediction.label
            dissent_evs = [ev for ev in dissent_evs + (local_evidences or []) if ev.prediction.label != agreed_lab]
            if dissent_evs:
                best_d = PredictionMerger.select_strongest(dissent_evs)
                if PredictionMerger.is_stronger(best_d, consensus_ev):
                    return TokenDecision.create_with_trace(best_d.prediction.label, best_d.model, f"Local context selected {best_d.prediction.label}.", competing, merged_dist or best_d.prediction.res_dist, token_str, m_preds, DecisionStage.LOCAL_CONTEXT)
                else:
                    return TokenDecision.create_with_trace(consensus_ev.prediction.label, consensus_ev.model, f"Consensus retained {agreed_lab}.", competing, merged_dist or consensus_ev.prediction.res_dist, token_str, m_preds, DecisionStage.EVIDENCE_COMPARISON)
            return TokenDecision.create_with_trace(consensus_ev.prediction.label, consensus_ev.model, f"Consensus agreed on {agreed_lab}.", competing, merged_dist or consensus_ev.prediction.res_dist, token_str, m_preds, DecisionStage.CONSENSUS)

        best_ev = PredictionMerger.select_strongest(all_ev)
        return TokenDecision.create_with_trace(best_ev.prediction.label, best_ev.model, f"Evidence comparison selected {best_ev.prediction.label}.", competing, merged_dist or best_ev.prediction.res_dist, token_str, m_preds, DecisionStage.LOCAL_CONTEXT)


class DecisionMaker:
    @staticmethod
    def make_decisions(
        segments: List[Tuple[str, str, int, int]],
        token_predictions: List[List[ModelPrediction]],
        candidate_langs: Set[str],
        models: List[BaseLanguageModel],
        text: str = "",
        enable_context: bool = True,
        context_everywhere: bool = False
    ) -> List[TokenDecision]:
        scripts = [seg[1] for seg in segments]
        results: List[TokenDecision] = []

        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            preds = token_predictions[idx]
            boundary_ev, evidences = PredictionAnalyzer.analyze_and_validate(preds, idx, scripts, token_str, candidate_langs)
            local_evidences = None
            if enable_context and ContextChecker.should_trigger(token_str, None, boundary_ev, evidences, context_everywhere=context_everywhere):
                local_evidences = ContextChecker.analyze(idx, segments, candidate_langs, models, boundary_ev, text, token_predictions)
            decision = DecisionEngine.arbitrate(evidences, idx, segments, boundary_ev, local_evidences)
            results.append(decision)
        return results


# ------------------------------------------------------------------------------
# 5. RESULT REFINER: Result clean-up & span assembly
# ------------------------------------------------------------------------------
class ResultRefiner:
    CLAUSE_DELIMITERS = CLAUSE_BREAKS

    @staticmethod
    def should_preserve_single_token_switch(
        decision: TokenDecision,
        switch_label: str,
        matrix_label: str,
        token: str,
    ) -> bool:
        switch_score = decision.distribution.get(switch_label, 0.0)
        matrix_score = decision.distribution.get(matrix_label, 0.0)

        model_votes = Counter(
            label
            for _, label in decision.competing_predictions
            if label
        )

        independent_support = model_votes.get(switch_label, 0)

        if len(token) <= 2:
            return (
                independent_support >= 2
                and switch_score >= 0.90
                and decision.margin >= 0.55
                and matrix_score <= 0.10
            )

        if len(token) == 3:
            return (
                independent_support >= 2
                and switch_score >= 0.82
                and decision.margin >= 0.40
            )

        return (
            independent_support >= 2
            or decision.margin >= 0.35
            or (switch_score >= 0.75 and matrix_score <= 0.15)
        )

    @staticmethod
    def refine_and_assemble(
        text: str,
        segments: List[Tuple[str, str, int, int]],
        decisions: List[TokenDecision],
        enable_refinement: bool = True,
        enable_short_span_absorption: bool = False,
        enable_generic_aba_gating: bool = True,
    ) -> Tuple[List[TokenDecision], List[Tuple[str, str]], List[Dict]]:
        n = len(decisions)
        if n == 0:
            return [], [(text, 'en')], []

        smoothed = list(decisions)
        for i in range(n):
            if segments[i][1] == "ENTITY":
                nbr_idx = i + 1 if i + 1 < n and segments[i+1][1] != "ENTITY" else (i - 1 if i > 0 and segments[i-1][1] != "ENTITY" else i)
                smoothed[i].label = smoothed[nbr_idx].label if smoothed[nbr_idx].label != "und" else "en"

        if enable_refinement:
            # 1. Macro-clause Contextualization (Solution 5)
            clauses = []
            cur_clause = []
            for i in range(n):
                tok_str = segments[i][0]
                cur_clause.append(i)
                gap = text[segments[i][3]:segments[i+1][2]] if (i + 1 < n and text) else ""
                is_delimiter = (
                    any(c in ResultRefiner.CLAUSE_DELIMITERS for c in gap)
                    or (not any(c.isalnum() for c in tok_str) and (tok_str in ResultRefiner.CLAUSE_DELIMITERS or any(c in ResultRefiner.CLAUSE_DELIMITERS for c in tok_str)))
                )
                if is_delimiter:
                    clauses.append(cur_clause)
                    cur_clause = []
            if cur_clause:
                clauses.append(cur_clause)

            token_clause_matrix = {}
            for clause in clauses:
                content_tokens = [smoothed[idx] for idx in clause if segments[idx][1] != "ENTITY" and any(c.isalnum() for c in segments[idx][0])]
                if not content_tokens:
                    continue
                counts = Counter(d.label for d in content_tokens)
                top_lang, top_count = counts.most_common(1)[0]
                clause_ratio = top_count / len(content_tokens)
                if clause_ratio >= 0.60 and len(content_tokens) >= 3:
                    matrix_lang = top_lang
                    for idx in clause:
                        cur_dec = smoothed[idx]
                        token_script = segments[idx][1]
                        allowed_for_sc = SCRIPT_TO_LANGUAGES.get(token_script, {matrix_lang})
                        if matrix_lang not in allowed_for_sc:
                            continue
                        if token_script != "ENTITY" and cur_dec.label != matrix_lang:
                            tok_str = segments[idx][0]
                            p_mat = cur_dec.distribution.get(matrix_lang, 0.0)
                            p_cand = cur_dec.distribution.get(cur_dec.label, 0.0)
                            bayes_mat = p_mat * (clause_ratio ** 0.35)
                            bayes_cand = p_cand * ((1.0 - clause_ratio) ** 0.35)
                            should_smooth = (
                                bayes_mat > bayes_cand
                                or (p_mat >= 0.15 and p_cand < 0.45)
                                or cur_dec.margin < 0.25
                            )
                            if should_smooth:
                                nd = dict(cur_dec.distribution)
                                nd[matrix_lang] = max(nd.get(matrix_lang, 0.0), 0.85)
                                smoothed[idx] = TokenDecision.create_with_trace(
                                    matrix_lang,
                                    cur_dec.decided_by + '+ClauseMatrixSmoothing',
                                    f'Clause matrix {matrix_lang} resolved solitary outlier {cur_dec.label}.',
                                    cur_dec.competing_predictions, nd, tok_str,
                                    cur_dec.trace.model_predictions if cur_dec.trace else {},
                                    DecisionStage.CONTEXT_REFINEMENT
                                )

            # Sentence-level Matrix Language prior for solitary short tokens
            all_content = [smoothed[i] for i in range(n) if segments[i][1] != "ENTITY" and any(c.isalnum() for c in segments[i][0])]
            if len(all_content) >= 5:
                sent_counts = Counter(d.label for d in all_content)
                sent_top_lang, sent_top_count = sent_counts.most_common(1)[0]
                if sent_top_count / len(all_content) >= 0.75:
                    sent_matrix = sent_top_lang
                    for i in range(n):
                        tok_s = segments[i][0]
                        sc = segments[i][1]
                        if len(tok_s) <= 3 and smoothed[i].label != sent_matrix and sc in SCRIPT_TO_LANGUAGES and sent_matrix in SCRIPT_TO_LANGUAGES[sc]:
                            p_sm = smoothed[i].distribution.get(sent_matrix, 0.0)
                            p_scand = smoothed[i].distribution.get(smoothed[i].label, 0.0)
                            if smoothed[i].margin < 0.25 or (p_sm >= 0.12 and p_scand < 0.50):
                                nd = dict(smoothed[i].distribution)
                                nd[sent_matrix] = max(nd.get(sent_matrix, 0.0), 0.85)
                                smoothed[i] = TokenDecision.create_with_trace(
                                    sent_matrix,
                                    smoothed[i].decided_by + '+SentenceMatrixSmoothing',
                                    f'Sentence matrix {sent_matrix} smoothed solitary token {smoothed[i].label}.',
                                    smoothed[i].competing_predictions, nd, tok_s,
                                    smoothed[i].trace.model_predictions if smoothed[i].trace else {},
                                    DecisionStage.CONTEXT_REFINEMENT
                                )

            # 2. Two-Pass Bidirectional Right-Left Switch Validation
            for _ in range(2):
                new_s = list(smoothed)
                for i in range(1, n - 1):
                    p_dec, c_dec, n_dec = smoothed[i-1], smoothed[i], smoothed[i+1]
                    p_script, c_script, n_script = segments[i-1][1], segments[i][1], segments[i+1][1]

                    # Physical Unicode script boundaries are absolute
                    if not (p_script == c_script == n_script):
                        continue

                    # A - B - A solitary sandwich switch pattern
                    if p_dec.label == n_dec.label and p_dec.label != c_dec.label:
                        matrix_lab = p_dec.label
                        cand_lab = c_dec.label
                        tok = segments[i][0]

                        p_cand = c_dec.distribution.get(cand_lab, 0.0)

                        if enable_generic_aba_gating:
                            pass_switch = ResultRefiner.should_preserve_single_token_switch(
                                decision=c_dec,
                                switch_label=cand_lab,
                                matrix_label=matrix_lab,
                                token=tok,
                            )
                        else:
                            pass_switch = (p_cand >= 0.80)

                        if not pass_switch:
                            nd = dict(c_dec.distribution)
                            nd[matrix_lab] = max(nd.get(matrix_lab, 0.0), p_cand)
                            new_s[i] = TokenDecision.create_with_trace(
                                matrix_lab,
                                c_dec.decided_by + '+BidirectionalConfidenceGating',
                                'Solitary switch ' + cand_lab + ' smoothed to ' + matrix_lab + '.',
                                c_dec.competing_predictions, nd, tok,
                                c_dec.trace.model_predictions if c_dec.trace else {},
                                DecisionStage.CONTEXT_REFINEMENT
                            )
                smoothed = new_s

            # 2b. Boundary Transition Solitary Token Smoothing (A - C - B)
            new_s = list(smoothed)
            for i in range(1, n - 1):
                p_dec, c_dec, n_dec = smoothed[i-1], smoothed[i], smoothed[i+1]
                p_script, c_script, n_script = segments[i-1][1], segments[i][1], segments[i+1][1]
                if not (p_script == c_script == n_script):
                    continue
                if p_dec.label != c_dec.label and n_dec.label != c_dec.label and p_dec.label != n_dec.label:
                    cand_lab = c_dec.label
                    tok = segments[i][0]
                    pass_switch = ResultRefiner.should_preserve_single_token_switch(
                        decision=c_dec,
                        switch_label=cand_lab,
                        matrix_label=p_dec.label,
                        token=tok,
                    )
                    if not pass_switch:
                        p_A = c_dec.distribution.get(p_dec.label, 0.0)
                        p_B = c_dec.distribution.get(n_dec.label, 0.0)
                        target_lab = p_dec.label if p_A >= p_B else n_dec.label
                        target_p = max(p_A, p_B)
                        if target_p >= 0.15:
                            nd = dict(c_dec.distribution)
                            nd[target_lab] = max(nd.get(target_lab, 0.0), 0.85)
                            new_s[i] = TokenDecision.create_with_trace(
                                target_lab,
                                c_dec.decided_by + '+BoundaryTransitionSmoothing',
                                f'Solitary boundary token {cand_lab} smoothed to adjacent {target_lab}.',
                                c_dec.competing_predictions, nd, tok,
                                c_dec.trace.model_predictions if c_dec.trace else {},
                                DecisionStage.CONTEXT_REFINEMENT
                            )
            smoothed = new_s

            # 3. Rare-language noise smoothing
            for i in range(n):
                c_dec = smoothed[i]
                tok = segments[i][0]
                lab = c_dec.label
                tok_len = len(tok)
                if tok_len <= 2 and lab in ('so', 'sl', 'la', 'eu', 'eo', 'cy', 'ga', 'is', 'af', 'zu', 'ca', 'sw', 'sk', 'ro', 'cs', 'et', 'nn'):
                    nbr_idx = i - 1 if i > 0 else (i + 1 if i < n - 1 else i)
                    nbr = smoothed[nbr_idx].label
                    if nbr != lab and segments[nbr_idx][1] == segments[i][1]:
                        nd = dict(c_dec.distribution)
                        nd[nbr] = 1.0
                        smoothed[i] = TokenDecision.create_with_trace(
                            nbr,
                            c_dec.decided_by + '+RareNoiseSmoothing',
                            'Rare noise smoothed to ' + nbr + '.',
                            c_dec.competing_predictions, nd, tok,
                            c_dec.trace.model_predictions if c_dec.trace else {},
                            DecisionStage.CONTEXT_REFINEMENT
                        )

        # ------------------------------------------------------------------
        # FIX 2: Short-Span Absorption (Optional Guarded Stage)
        # ------------------------------------------------------------------
        if enable_refinement and enable_short_span_absorption and n >= 3:
            for _absorption_pass in range(2):
                new_s = list(smoothed)
                i = 0
                while i < n:
                    j = i
                    while j < n and smoothed[j].label == smoothed[i].label:
                        j += 1
                    run_len = j - i
                    run_lang = smoothed[i].label
                    if run_len <= 2 and i > 0 and j < n:
                        prev_script = segments[i - 1][1]
                        run_scripts = set(segments[k][1] for k in range(i, j))
                        next_script = segments[j][1]
                        # Only absorb if no script boundary exists
                        if prev_script in run_scripts and next_script in run_scripts:
                            max_conf = max(smoothed[k].distribution.get(run_lang, 0.0) for k in range(i, j))
                            absorb_lang = smoothed[i - 1].label
                            absorb_conf = max(smoothed[k].distribution.get(absorb_lang, 0.0) for k in range(i, j))
                            # Tightened: only absorb when the run language is genuinely uncertain
                            # (max_conf < 0.55, previously 0.80) AND the absorbing language actually
                            # has higher probability in the model distribution.
                            # This preserves real single-token switches (English words inside Turkish
                            # like 'status', 'bulk', 'umbrella') while still absorbing true noise.
                            if max_conf < 0.55 and absorb_conf >= max_conf:
                                for k in range(i, j):
                                    nd = dict(smoothed[k].distribution)
                                    old_conf = nd.get(run_lang, 0.0)
                                    nd[absorb_lang] = max(nd.get(absorb_lang, 0.0), old_conf)
                                    new_s[k] = TokenDecision.create_with_trace(
                                        absorb_lang,
                                        smoothed[k].decided_by + '+ShortSpanAbsorption',
                                        f'Short span ({run_len} tok) absorbed into {absorb_lang}.',
                                        smoothed[k].competing_predictions, nd,
                                        segments[k][0],
                                        smoothed[k].trace.model_predictions if smoothed[k].trace else {},
                                        DecisionStage.CONTEXT_REFINEMENT
                                    )
                    i = j if j > i else i + 1
                smoothed = new_s

        for i in range(n):
            tok_s = segments[i][0]
            if not any(c.isalnum() for c in tok_s) or tok_s.isdigit():
                if tok_s.isdigit():
                    if i > 0 and i < n - 1 and smoothed[i - 1].label == smoothed[i + 1].label:
                        smoothed[i].label = smoothed[i - 1].label
                    elif i > 0:
                        smoothed[i].label = smoothed[i - 1].label
                    elif i < n - 1:
                        smoothed[i].label = smoothed[i + 1].label
                else:
                    nbr_idx = i - 1 if i > 0 else (i + 1 if i < n - 1 else i)
                    smoothed[i].label = smoothed[nbr_idx].label

        # 4. Token-level dictionary output
        token_dicts = []
        for i, dec in enumerate(smoothed):
            seg_str, sc, s_idx, e_idx = segments[i]
            token_dicts.append({
                'token': seg_str, 'label': dec.label,
                'confidence': float(dec.distribution.get(dec.label, 1.0)),
                'decided_by': dec.decided_by, 'reason': dec.reason,
                'start': s_idx, 'end': e_idx, 'script': sc
            })

        # 5. Spans merging
        spans: List[Tuple[str, str]] = []
        cur_lang, cur_start = smoothed[0].label, 0
        for i in range(1, n):
            lab = smoothed[i].label
            if lab != cur_lang:
                cut_idx = segments[i][2]
                spans.append((text[cur_start:cut_idx], cur_lang))
                cur_lang, cur_start = lab, cut_idx
        spans.append((text[cur_start:], cur_lang))

        return smoothed, spans, token_dicts


# ==============================================================================
# 5. MAIN PIPELINE
# ==============================================================================

class PolyLIDPipeline:
    """
    PolyLID Language Identification Pipeline:
      1. Tokenize text (Unicode scripts and boundaries)
      2. Find possible languages (GlotLID + FastText + Lingua)
      3. Classify each token (FastText + Lingua)
      4. Resolve conflicting predictions (DecisionEngine)
      5. Refine results and build spans (ResultRefiner)
    """
    def __init__(
        self,
        ft_path: str = "lid.176.ftz",
        enable_fasttext: bool = True,
        enable_lingua: bool = True,
        enable_glotlid: bool = True,
        enable_context: bool = True,
        enable_refinement: bool = True,
        enable_candidate_restriction: bool = True,
        enable_short_span_absorption: bool = False,
        enable_generic_aba_gating: bool = True,
        context_everywhere: bool = False,
        discovery_mode: str = "all",
    ):
        self.fasttext = FastTextModel(ft_path=ft_path) if enable_fasttext else None
        self.glotlid = GlotLIDModel() if enable_glotlid else None
        self.lingua = LinguaModel() if enable_lingua else None
        
        # Models for sentence-level discovery
        if discovery_mode == "none":
            self.discovery_models = []
        elif discovery_mode == "glotlid_only":
            self.discovery_models = [m for m in [self.glotlid] if m is not None]
        else: # "all"
            self.discovery_models = [m for m in [self.fasttext, self.glotlid, self.lingua] if m is not None]
            
        # Models for token-level classification (GlotLID kept out for efficiency)
        self.token_models = [m for m in [self.fasttext, self.lingua] if m is not None]
        
        self.enable_context = enable_context
        self.enable_refinement = enable_refinement
        self.enable_candidate_restriction = enable_candidate_restriction
        self.enable_short_span_absorption = enable_short_span_absorption
        self.enable_generic_aba_gating = enable_generic_aba_gating
        self.context_everywhere = context_everywhere

    def validate_runtime(self) -> None:
        failures = []

        if self.fasttext is not None and self.fasttext.model is None:
            failures.append("FastText was enabled but failed to load.")

        if self.glotlid is not None and self.glotlid.model is None:
            failures.append("GlotLID was enabled but failed to load.")

        if self.lingua is not None and self.lingua.model is None:
            failures.append("Lingua was enabled but failed to load.")

        if failures:
            raise RuntimeError(" ".join(failures))

    def detect_candidates(self, text: str) -> Set[str]:
        if not text or not text.strip():
            return set()

        segments = Tokenizer.segment(text)
        if not segments:
            return set()

        if not self.enable_candidate_restriction:
            return CandidateGenerator.get_candidates("all")

        return CandidateDetector.detect(
            text,
            self.discovery_models,
            segments=segments,
        )

    def _resolve_candidates(self, text: str, segments: Optional[List[Tuple[str, str, int, int]]] = None, allowed_langs: Optional[Any] = None) -> Set[str]:
        """Self-determined open-world candidate discovery.

        PolyLID operates fully autonomously in open-world mode. Candidate languages
        are self-determined directly from input text orthography, script runs, and
        multi-model consensus (GlotLID, FastText, Lingua) across all 66 supported
        languages and 12 writing scripts. External language constraints are bypassed.
        """
        return self.detect_candidates(text)

    def identify(self, text: str, allowed_langs: Optional[Any] = None) -> List[TokenDecision]:
        """Token-level language identification. Fully open-world and self-determined."""
        if not text or not text.strip():
            return []
        segments = Tokenizer.segment(text)
        if not segments:
            return []
        candidate_langs = self.detect_candidates(text)
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text, tiebreaker_model=self.glotlid)
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text, self.enable_context, self.context_everywhere)
        smoothed_decisions, _, _ = ResultRefiner.refine_and_assemble(
            text, segments, decisions, self.enable_refinement, self.enable_short_span_absorption, self.enable_generic_aba_gating
        )
        return smoothed_decisions

    def identify_to_dict(self, text: str, allowed_langs: Optional[Any] = None) -> List[Dict]:
        """Token-level language identification with full metadata per token. Fully open-world and self-determined."""
        if not text or not text.strip():
            return []
        segments = Tokenizer.segment(text)
        if not segments:
            return []
        candidate_langs = self.detect_candidates(text)
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text, tiebreaker_model=self.glotlid)
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text, self.enable_context, self.context_everywhere)
        _, _, token_dicts = ResultRefiner.refine_and_assemble(
            text, segments, decisions, self.enable_refinement, self.enable_short_span_absorption, self.enable_generic_aba_gating
        )
        return token_dicts

    def detect_languages(self, text: str, allowed_langs: Optional[Any] = None) -> List[Tuple[str, str]]:
        """Span-level language identification. Returns list of (span_text, lang_code) tuples.

        Fully open-world: Candidate languages are self-determined automatically via
        orthographic signatures and multi-model LID consensus. No language names needed externally.
        """
        if not text or not text.strip():
            return [(text, "en")]
        segments = Tokenizer.segment(text)
        if not segments:
            return [(text, "en")]
        candidate_langs = self.detect_candidates(text)
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text, tiebreaker_model=self.glotlid)
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text, self.enable_context, self.context_everywhere)
        _, spans, _ = ResultRefiner.refine_and_assemble(
            text, segments, decisions, self.enable_refinement, self.enable_short_span_absorption, self.enable_generic_aba_gating
        )
        return spans

    def predict(self, text: str, allowed_langs: Optional[Any] = None) -> List[Tuple[str, str]]:
        """Convenience alias for detect_languages."""
        return self.detect_languages(text, allowed_langs=allowed_langs)


PolyLID = PolyLIDPipeline
_detector = None

def get_detector(ft_path: str = "lid.176.ftz") -> PolyLIDPipeline:
    global _detector
    if _detector is None:
        _detector = PolyLIDPipeline(ft_path=ft_path)
    return _detector

def detect_languages(text: str, allowed_langs: Optional[Any] = None) -> List[Tuple[str, str]]:
    """Module-level convenience. Fully open-world auto-detection, no language hints needed."""
    return get_detector().detect_languages(text)

def batch_detect_languages(texts: List[str], allowed_langs: Optional[Any] = None) -> List[List[Tuple[str, str]]]:
    """Batch version of detect_languages. Fully open-world and self-determined."""
    det = get_detector()
    return [det.detect_languages(t) for t in texts]


__all__ = [
    "PolyLID", "PolyLIDPipeline", "get_detector", "detect_languages", "batch_detect_languages",
    "Tokenizer", "CandidateDetector", "TokenClassifier", "DecisionMaker", "ResultRefiner",
    "DecisionEngine", "PredictionAnalyzer", "PredictionMerger", "ContextChecker",
    "BaseLanguageModel", "FastTextModel", "GlotLIDModel", "LinguaModel",
    "ModelPrediction", "PredictionEvidence", "TokenDecision", "DecisionTrace", "DecisionStage",
    "CandidateGenerator", "SUPPORTED_LANGS", "LANG_NAME_TO_CODE", "SCRIPT_RANGES",
    "SCRIPT_TO_DEFAULT_LANG", "SCRIPT_TO_LANGUAGES"
]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PolyLID: Code-Switching Language Identification Engine")
    parser.add_argument("text", nargs="?", default="Hello friend, cómo estás? Everything is fine aquí.", help="Text to analyze")
    args = parser.parse_args()

    print(f"\n=== PolyLID Code-Switching LID ===")
    print(f"Input: {args.text}")
    detector = get_detector()
    res = detector.detect_languages(args.text)
    print("\nDetected Spans:")
    for span_text, lang in res:
        print(f"  [{lang.upper()}]: {repr(span_text)}")


