from __future__ import annotations

import importlib
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
    "zh", "ja", "ko", "th", "vi", "id", "ms", "tl",
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
    "GUJARATI": "gu", "GURMUKHI": "pa", "KANNADA": "kn", "MALAYALAM": "ml",
    "ORIYA": "or", "TAMIL": "ta", "TELUGU": "te", "THAI": "th",
    "HANGUL": "ko", "HIRAGANA": "ja", "KATAKANA": "ja", "HAN": "zh",
    "GREEK": "el", "HEBREW": "he", "GEORGIAN": "ka", "ARMENIAN": "hy",
}

SCRIPT_TO_LANGUAGES = {
    "BENGALI": {"bn"}, "DEVANAGARI": {"hi", "mr", "ne"}, "ARABIC": {"ar", "ur", "fa"},
    "CYRILLIC": {"ru", "bg", "uk", "be", "sr", "mk", "kk"},
    "LATIN": {"en", "es", "tr", "fr", "de", "it", "pt", "nl", "pl", "cs", "ro", "sv", "vi", "id", "ms", "da", "fi", "hu", "no", "sk", "sl", "hr", "ca", "eu", "et", "lv", "lt", "is", "ga", "cy", "la", "eo", "sq", "af", "sw", "so", "yo", "zu", "xh", "az", "tl"},
    "HAN": {"zh", "ja"}, "HIRAGANA": {"ja"}, "KATAKANA": {"ja"}, "HANGUL": {"ko"},
    "THAI": {"th"}, "GUJARATI": {"gu"}, "GURMUKHI": {"pa"}, "KANNADA": {"kn"},
    "MALAYALAM": {"ml"}, "ORIYA": {"or"}, "TAMIL": {"ta"}, "TELUGU": {"te"},
    "GREEK": {"el"}, "HEBREW": {"he"}, "GEORGIAN": {"ka"}, "ARMENIAN": {"hy"},
}

LANG_NAME_TO_CODE = {
    "arabic": "ar", "bulgarian": "bg", "bengali": "bn", "bangla": "bn", "german": "de",
    "english": "en", "spanish": "es", "french": "fr", "gujarati": "gu",
    "hindi": "hi", "indonesian": "id", "italian": "it", "japanese": "ja",
    "korean": "ko", "dutch": "nl", "polish": "pl", "portuguese": "pt",
    "russian": "ru", "tamil": "ta", "telugu": "te", "thai": "th", "turkish": "tr",
    "urdu": "ur", "vietnamese": "vi", "chinese": "zh", "mandarin": "zh",
    "marathi": "mr", "nepali": "ne", "punjabi": "pa", "persian": "fa", "farsi": "fa",
    "greek": "el", "hebrew": "he", "romanian": "ro", "swedish": "sv", "czech": "cs",
    "ukrainian": "uk", "danish": "da", "finnish": "fi", "hungarian": "hu",
    "slovak": "sk", "slovene": "sl", "catalan": "ca", "basque": "eu", "croatian": "hr",
    "serbian": "sr", "estonian": "et", "latvian": "lv", "lithuanian": "lt",
    "icelandic": "is", "irish": "ga", "welsh": "cy", "latin": "la", "esperanto": "eo",
    "albanian": "sq", "macedonian": "mk", "belarusian": "be", "afrikaans": "af",
    "swahili": "sw", "somali": "so", "yoruba": "yo", "zulu": "zu", "xhosa": "xh",
    "azerbaijani": "az", "georgian": "ka", "armenian": "hy", "kazakh": "kk",
    "malay": "ms", "tagalog": "tl"
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
    "SWAHILI": "sw", "SOMALI": "so", "YORUBA": "yo", "ZULU": "zu", "XHOSA": "xh",
    "AZERBAIJANI": "az", "GEORGIAN": "ka", "ARMENIAN": "hy", "KAZAKH": "kk",
    "MALAY": "ms", "TAGALOG": "tl", "BOSNIAN": "bs", "NYNORSK": "nn", "BOKMAL": "nb"
}

GLOTLID_MAP = {
    'eng': 'en', 'spa': 'es', 'por': 'pt', 'fra': 'fr', 'ita': 'it', 
    'deu': 'de', 'tur': 'tr', 'zho': 'zh', 'cmn': 'zh', 'hin': 'hi', 
    'rus': 'ru', 'jpn': 'ja', 'kor': 'ko', 'ind': 'id', 'nld': 'nl',
    'pol': 'pl', 'ben': 'bn', 'tam': 'ta', 'tel': 'te', 'guj': 'gu',
    'tha': 'th', 'vie': 'vi', 'ara': 'ar', 'arb': 'ar', 'bul': 'bg',
    'urd': 'ur', 'mar': 'mr', 'nep': 'ne', 'npi': 'ne', 'pan': 'pa',
    'fas': 'fa', 'pes': 'fa', 'ell': 'el', 'heb': 'he', 'ron': 'ro',
    'swe': 'sv', 'ces': 'cs', 'ukr': 'uk', 'dan': 'da', 'fin': 'fi',
    'hun': 'hu', 'slk': 'sk', 'slv': 'sl', 'cat': 'ca', 'eus': 'eu',
    'hrv': 'hr', 'srp': 'sr', 'est': 'et', 'lav': 'lv', 'lit': 'lt',
    'isl': 'is', 'gle': 'ga', 'cym': 'cy', 'lat': 'la', 'epo': 'eo',
    'sqi': 'sq', 'mkd': 'mk', 'bel': 'be', 'afr': 'af', 'swh': 'sw',
    'som': 'so', 'yor': 'yo', 'zul': 'zu', 'xho': 'xh', 'azj': 'az',
    'kat': 'ka', 'hye': 'hy', 'kaz': 'kk', 'zsm': 'ms', 'tgl': 'tl',
    'bos': 'bs', 'nob': 'nb', 'nno': 'nn', 'kan': 'kn', 'mal': 'ml',
    'ory': 'or', 'asm': 'as', 'san': 'sa', 'snd': 'sd'
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
    return "UNKNOWN"

def dominant_script(text: str) -> str:
    votes = Counter()
    for ch in text:
        if ch.isalpha():
            votes[get_script(ch)] += 1
    return votes.most_common(1)[0][0] if votes else "UNKNOWN"

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
        if allowed_langs is None or allowed_langs == "all":
            return SUPPORTED_LANGS
        if isinstance(allowed_langs, str):
            return {normalize_lang_code(allowed_langs)}
        return {normalize_lang_code(l) for l in allowed_langs if l}

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
            text_cln = text.replace('\n', ' ')
            predictions = self.model.f.predict(text_cln, 12, 0.0, "strict")
            raw = {normalize_lang_code(l): float(p) for p, l in zip(*predictions) if normalize_lang_code(l)} if predictions else {}
            dist = normalize_probs(raw)
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)


class GlotLIDModel(BaseLanguageModel):
    def __init__(self):
        super().__init__("GlotLID")
        self.model = None
        ft_mod = require("fasttext")
        try:
            hf_cache = os.path.expanduser("~/.cache/huggingface/hub/models--cis-lmu--glotlid/snapshots")
            glotlid_path = ""
            if os.path.exists(hf_cache):
                snaps = os.listdir(hf_cache)
                if snaps:
                    glotlid_path = os.path.join(hf_cache, snaps[0], "model.bin")
            if ft_mod is not None and glotlid_path and os.path.exists(glotlid_path):
                self.model = ft_mod.load_model(glotlid_path)
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
            text_cln = text.replace('\n', ' ')
            predictions = self.model.f.predict(text_cln, 15, 0.0, "strict")
            raw = {}
            if predictions:
                probs, labels = zip(*predictions)
                for l, p in zip(labels, probs):
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
class Tokenizer:
    @staticmethod
    def segment(text: str) -> List[Tuple[str, str, int, int]]:
        if not text:
            return []
        parts = []
        buf = []
        last_script = ""
        start_idx = 0
        
        for i, ch in enumerate(text):
            category = unicodedata.category(ch)
            is_internal_punc = (
                ch in {"'", "-", "â€™"}
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

        for ch in text:
            sc = get_script(ch)
            if sc == "LATIN": has_latin = True
            elif sc == "HAN": has_han = True
            elif sc in ("HIRAGANA", "KATAKANA"): has_kana = True
            elif sc == "ARABIC": has_arabic = True
            elif sc == "CYRILLIC": has_cyrillic = True
            elif sc == "DEVANAGARI": has_devanagari = True
            elif sc == "BENGALI": has_bengali = True
            elif sc in SCRIPT_TO_DEFAULT_LANG:
                D.add(SCRIPT_TO_DEFAULT_LANG[sc])

        if has_kana: D.add("ja")
        if has_han:
            D.add("zh")
            if has_kana: D.add("ja")
        if has_bengali: D.add("bn")

        if has_devanagari and glotlid:
            dev_runs = [seg[0] for seg in segments if seg[1] == "DEVANAGARI"]
            dev_text = " ".join(dev_runs)
            d_preds = glotlid.predict(dev_text or text, ["hi", "mr", "ne"])
            if d_preds:
                top_d, top_dp = max(d_preds.items(), key=lambda x: x[1])
                D.add(top_d)
                min_dp = 0.45 if top_dp >= 0.55 else 0.35
                for l, p in d_preds.items():
                    if l != top_d and p >= min_dp: D.add(l)
            else:
                D.add("hi")

        if has_arabic:
            if any(c in text for c in ['\u06D2', '\u0679', '\u0688', '\u0691', '\u06C1', '\u06BE', '\u06BA']):
                D.add("ur")
            elif any(c in text for c in ['\u067E', '\u0686', '\u0698', '\u06AF', '\u06CC']):
                D.add("fa")
            elif glotlid:
                ar_runs = [seg[0] for seg in segments if seg[1] == "ARABIC"]
                ar_text = " ".join(ar_runs)
                a_preds = glotlid.predict(ar_text or text, ["ar", "ur", "fa"])
                if a_preds:
                    top_a, top_ap = max(a_preds.items(), key=lambda x: x[1])
                    D.add(top_a)
                    min_ap = 0.45 if top_ap >= 0.55 else 0.35
                    for l, p in a_preds.items():
                        if l != top_a and p >= min_ap: D.add(l)
                else:
                    D.add("ar")
            else:
                D.add("ar")

        if has_cyrillic and glotlid:
            cyr_runs = [seg[0] for seg in segments if seg[1] == "CYRILLIC"]
            cyr_text = " ".join(cyr_runs)
            c_preds = glotlid.predict(cyr_text or text, ["ru", "bg", "uk", "be", "sr", "mk", "kk"])
            if c_preds:
                top_c, top_cp = max(c_preds.items(), key=lambda x: x[1])
                D.add(top_c)
                min_cp = 0.45 if top_cp >= 0.55 else 0.35
                for l, p in c_preds.items():
                    if l != top_c and p >= min_cp: D.add(l)
            else:
                D.add("ru")

        if has_latin:
            D.add("en")
            latin_runs = [seg[0] for seg in segments if seg[1] == "LATIN"]
            latin_text = " ".join(latin_runs)
            if glotlid and latin_text:
                g_preds = glotlid.predict(latin_text, None)
                sorted_g = sorted(g_preds.items(), key=lambda x: x[1], reverse=True)
                if sorted_g:
                    top_l, top_p = sorted_g[0]
                    D.add(top_l)
                    min_p = 0.35 if top_p >= 0.55 else 0.20
                    for l, p in sorted_g[1:4]:
                        if p >= min_p: D.add(l)
            if lingua and latin_text:
                l_preds = lingua.predict(latin_text, None)
                sorted_l = sorted(l_preds.items(), key=lambda x: x[1], reverse=True)
                if sorted_l:
                    top_l, top_p = sorted_l[0]
                    D.add(top_l)
                    min_p = 0.35 if top_p >= 0.55 else 0.20
                    for l, p in sorted_l[1:3]:
                        if p >= min_p: D.add(l)
            if len(latin_runs) >= 4:
                for i in range(0, len(latin_runs) - 3, 3):
                    chunk = " ".join(latin_runs[i:i+4])
                    ft_preds = fasttext.predict(chunk, None) if fasttext else {}
                    top_ft, ft_p = top_label(ft_preds) if ft_preds else ("", 0.0)
                    if top_ft in D and ft_p >= 0.70:
                        continue
                    g_chunk = glotlid.predict(chunk, None) if glotlid else {}
                    l_chunk = lingua.predict(chunk, None) if lingua else {}
                    for l, gp in sorted(g_chunk.items(), key=lambda x: x[1], reverse=True)[:2]:
                        lp = l_chunk.get(l, 0.0)
                        min_req = 0.45 if l in ("ca", "zu", "sl", "af", "cy", "pt") else 0.38
                        if gp >= min_req and lp >= 0.20:
                            D.add(l)
                    for l, lp in sorted(l_chunk.items(), key=lambda x: x[1], reverse=True)[:2]:
                        gp = g_chunk.get(l, 0.0)
                        min_req = 0.48 if l in ("ca", "zu", "sl", "af", "cy", "pt") else 0.42
                        if lp >= min_req and gp >= 0.20:
                            D.add(l)

            # Sister language mutual suppression using already-computed g_preds
            if "id" in D and "ms" in D:
                s_id = g_preds.get("id", 0.0) if glotlid else 0.0
                s_ms = g_preds.get("ms", 0.0) if glotlid else 0.0
                if s_id >= s_ms: D.discard("ms")
                else: D.discard("id")

            if "ca" in D:
                if not any(c in latin_text.lower() for c in ('lÂ·l', 'Â·', 'ny', 'Ã§')):
                    if "es" in D or "fr" in D or "pt" in D:
                        D.discard("ca")

            if "es" in D and "pt" in D and "it" not in D:
                s_es = g_preds.get("es", 0.0) if glotlid else 0.0
                s_pt = g_preds.get("pt", 0.0) if glotlid else 0.0
                if s_es >= 0.40 and s_es >= s_pt: D.discard("pt")
                elif s_pt >= 0.40 and s_pt > s_es: D.discard("es")

            if "pt" in D and "en" in D and "es" not in D and "it" not in D:
                s_en = g_preds.get("en", 0.0) if glotlid else 0.0
                s_pt = g_preds.get("pt", 0.0) if glotlid else 0.0
                if s_en >= 0.40 and s_pt <= 0.30:
                    D.discard("pt")

            if "cy" in D and "en" in D:
                if not any(c in latin_text.lower() for c in ('Åµ', 'Å·', 'dd', 'ff', 'll', 'rh')):
                    D.discard("cy")

            if "sl" in D and "en" in D:
                s_en = g_preds.get("en", 0.0) if glotlid else 0.0
                s_sl = g_preds.get("sl", 0.0) if glotlid else 0.0
                if s_en >= 0.40 and s_sl <= 0.25:
                    D.discard("sl")

            if "zu" in D and "en" in D:
                D.discard("zu")

        return D or {"en"}


# ------------------------------------------------------------------------------
# 3. TOKEN CLASSIFIER: Token-level classification & local window context
# ------------------------------------------------------------------------------
class TokenClassifier:
    @staticmethod
    def classify_tokens(
        segments: List[Tuple[str, str, int, int]],
        candidate_langs: Set[str],
        models: List[BaseLanguageModel],
        text: str = ""
    ) -> List[List[ModelPrediction]]:
        clause_has_kana = []
        for i, (tok_str, script, start_idx, end_idx) in enumerate(segments):
            c_start = i
            while c_start > 0:
                gap = text[segments[c_start - 1][3]:segments[c_start][2]] if text else ""
                if any(p in gap for p in 'â€”\n.!?;'): break
                c_start -= 1
            c_end = i + 1
            while c_end < len(segments):
                gap = text[segments[c_end - 1][3]:segments[c_end][2]] if text else ""
                if any(p in gap for p in 'â€”\n.!?;'): break
                c_end += 1
            clause_has_kana.append(any(segments[k][1] in ("HIRAGANA", "KATAKANA") for k in range(c_start, c_end)))

        token_predictions: List[List[ModelPrediction]] = []
        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            preds: List[ModelPrediction] = []
            clean_tok = token_str.strip('.,!?;:"\'()[]{}â€”') or token_str

            if clause_has_kana[idx] and script == "HAN":
                preds.append(ModelPrediction("ja", 0.99, 0.99, [("ja", 0.99)], "JapaneseKanjiTopology", {"ja": 0.99}, {"ja": 0.99}))
                token_predictions.append(preds)
                continue

            token_allowed = candidate_langs & SCRIPT_TO_LANGUAGES.get(script, candidate_langs)
            if not token_allowed:
                token_allowed = SCRIPT_TO_LANGUAGES.get(script, candidate_langs)

            # 3-token window context string
            w_start, w_end = max(0, idx - 1), min(len(segments), idx + 2)
            window_toks = [segments[w_i][0] for w_i in range(w_start, w_end) if segments[w_i][1] == script]
            window_str = " ".join(window_toks) if len(window_toks) > 1 else clean_tok

            for model in models:
                if model.supports_token(clean_tok, script, token_allowed):
                    raw_dist, res_dist = model.evaluate(clean_tok, token_allowed)
                    if len(clean_tok) <= 3 or not res_dist or top_label(res_dist)[2] < 0.25:
                        if window_str != clean_tok:
                            _, win_dist = model.evaluate(window_str, token_allowed)
                            if win_dist:
                                res_dist, raw_dist = win_dist, win_dist

                    if res_dist:
                        lab, conf, margin = top_label(res_dist)
                        ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                        preds.append(ModelPrediction(lab, conf, margin, ranked, model.name, raw_dist, res_dist))
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
    def should_trigger(token_str, consensus_ev, boundary_ev, evidences):
        if not token_str or len(token_str) < 2 or not token_str.isalpha(): return False
        if boundary_ev.needs_arbitration: return True
        if evidences:
            best = PredictionMerger.select_strongest(evidences)
            if best.margin <= 0.25 or len(token_str) <= 3: return True
        return False

    @staticmethod
    def analyze(token_idx, segments, candidate_langs, models, boundary_ev, text="", token_predictions=None):
        if not segments or not (0 <= token_idx < len(segments)): return []
        token_str, script, _, _ = segments[token_idx]
        start_w = token_idx
        while start_w > 0 and segments[start_w - 1][1] == script and (token_idx - start_w) < 2:
            gap = text[segments[start_w - 1][3]:segments[start_w][2]] if text else ""
            if any(p in gap for p in '.,!?;:â€”'): break
            start_w -= 1
        end_w = token_idx + 1
        while end_w < len(segments) and segments[end_w][1] == script and (end_w - token_idx) <= 2:
            gap = text[segments[end_w - 1][3]:segments[end_w][2]] if text else ""
            if any(p in gap for p in '.,!?;:â€”'): break
            end_w += 1

        local_evidences: List[PredictionEvidence] = []
        def evaluate_phrase(phrase_str, prefix):
            for model in models:
                if model.supports_token(token_str, script, candidate_langs):
                    raw_dist, res_dist = model.evaluate(phrase_str, candidate_langs)
                    if res_dist:
                        lab, conf, margin = top_label(res_dist)
                        ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                        m_name = f"LocalContext{prefix}({model.name})"
                        pred = ModelPrediction(lab, conf, margin, ranked, m_name, raw_dist, res_dist)
                        local_evidences.append(PredictionEvidence(m_name, pred, margin, conf, boundary_ev, 1, script, token_str, ranked))

        if start_w < token_idx: evaluate_phrase(" ".join(segments[i][0] for i in range(start_w, token_idx + 1)), "Left")
        if end_w > token_idx + 1: evaluate_phrase(" ".join(segments[i][0] for i in range(token_idx, end_w)), "Right")
        if start_w < token_idx and end_w > token_idx + 1: evaluate_phrase(" ".join(segments[i][0] for i in range(start_w, end_w)), "Combined")

        lc = Counter(e.prediction.label for e in local_evidences)
        for e in local_evidences: e.agreement_count = lc[e.prediction.label]
        return local_evidences


class PredictionMerger:
    @staticmethod
    def is_stronger(ev1: PredictionEvidence, ev2: PredictionEvidence) -> bool:
        if ev1.agreement_count != ev2.agreement_count:
            return ev1.agreement_count > ev2.agreement_count
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
        all_ev = list(evidences) + (local_evidences or [])
        if not all_ev:
            default_lang = SCRIPT_TO_DEFAULT_LANG.get(script, "en")
            return TokenDecision.create_with_trace(default_lang, "DefaultScriptPrior", f"Defaulted to {default_lang}.", [], {default_lang: 1.0}, token_str, {}, DecisionStage.DETERMINISTIC_SCRIPT)

        competing = [(ev.model, ev.prediction.label) for ev in all_ev]
        m_preds = {ev.model: ev.prediction.label for ev in all_ev}

        if not boundary_ev.needs_arbitration and not local_evidences:
            best_ev = PredictionMerger.select_strongest(evidences)
            stage = DecisionStage.UNANIMOUS if len(evidences) >= 2 or best_ev.agreement_count >= 2 else DecisionStage.EVIDENCE_COMPARISON
            return TokenDecision.create_with_trace(best_ev.prediction.label, best_ev.model, f"Selected {best_ev.prediction.label}.", competing, best_ev.prediction.res_dist, token_str, m_preds, stage)

        consensus_ev, dissent_evs = PredictionMerger.fuse_consensus(evidences, boundary_ev)
        if consensus_ev is not None:
            agreed_lab = consensus_ev.prediction.label
            dissent_evs = [ev for ev in dissent_evs + (local_evidences or []) if ev.prediction.label != agreed_lab]
            if dissent_evs:
                best_d = PredictionMerger.select_strongest(dissent_evs)
                if PredictionMerger.is_stronger(best_d, consensus_ev):
                    return TokenDecision.create_with_trace(best_d.prediction.label, best_d.model, f"Local context selected {best_d.prediction.label}.", competing, best_d.prediction.res_dist, token_str, m_preds, DecisionStage.LOCAL_CONTEXT)
                else:
                    return TokenDecision.create_with_trace(consensus_ev.prediction.label, consensus_ev.model, f"Consensus retained {agreed_lab}.", competing, consensus_ev.prediction.res_dist, token_str, m_preds, DecisionStage.EVIDENCE_COMPARISON)
            return TokenDecision.create_with_trace(consensus_ev.prediction.label, consensus_ev.model, f"Consensus agreed on {agreed_lab}.", competing, consensus_ev.prediction.res_dist, token_str, m_preds, DecisionStage.CONSENSUS)

        best_ev = PredictionMerger.select_strongest(all_ev)
        return TokenDecision.create_with_trace(best_ev.prediction.label, best_ev.model, f"Evidence comparison selected {best_ev.prediction.label}.", competing, best_ev.prediction.res_dist, token_str, m_preds, DecisionStage.LOCAL_CONTEXT)


class DecisionMaker:
    @staticmethod
    def make_decisions(
        segments: List[Tuple[str, str, int, int]],
        token_predictions: List[List[ModelPrediction]],
        candidate_langs: Set[str],
        models: List[BaseLanguageModel],
        text: str = ""
    ) -> List[TokenDecision]:
        scripts = [seg[1] for seg in segments]
        results: List[TokenDecision] = []

        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            preds = token_predictions[idx]
            boundary_ev, evidences = PredictionAnalyzer.analyze_and_validate(preds, idx, scripts, token_str, candidate_langs)
            local_evidences = None
            if ContextChecker.should_trigger(token_str, None, boundary_ev, evidences):
                local_evidences = ContextChecker.analyze(idx, segments, candidate_langs, models, boundary_ev, text, token_predictions)
            decision = DecisionEngine.arbitrate(evidences, idx, segments, boundary_ev, local_evidences)
            results.append(decision)
        return results


# ------------------------------------------------------------------------------
# 5. RESULT REFINER: Result clean-up & span assembly
# ------------------------------------------------------------------------------
class ResultRefiner:
    @staticmethod
    def refine_and_assemble(
        text: str,
        segments: List[Tuple[str, str, int, int]],
        decisions: List[TokenDecision]
    ) -> Tuple[List[TokenDecision], List[Tuple[str, str]], List[Dict]]:
        n = len(decisions)
        if n == 0:
            return [], [(text, "en")], []

        # 1. Non-destructive smoothing
        smoothed = list(decisions)
        for _ in range(2):
            new_s = list(smoothed)
            for i in range(1, n - 1):
                p_dec, c_dec, n_dec = smoothed[i-1], smoothed[i], smoothed[i+1]
                if segments[i-1][1] == segments[i][1] == segments[i+1][1] and p_dec.label == n_dec.label != c_dec.label:
                    tok = segments[i][0]
                    if len(tok) <= 3 or c_dec.margin <= 0.35 or c_dec.distribution.get(p_dec.label, 0.0) >= 0.05:
                        nd = dict(c_dec.distribution)
                        nd[p_dec.label] = max(nd.get(p_dec.label, 0.0), c_dec.distribution.get(c_dec.label, 0.0))
                        new_s[i] = TokenDecision.create_with_trace(
                            p_dec.label, f"{c_dec.decided_by}+ContextRefinement",
                            f"Bounded by identical {p_dec.label} neighbors.",
                            c_dec.competing_predictions, nd, tok, c_dec.trace.model_predictions if c_dec.trace else {},
                            DecisionStage.CONTEXT_REFINEMENT
                        )
            smoothed = new_s

        # 2. Smooth isolated short noise tokens
        for i in range(n):
            c_dec = smoothed[i]
            tok = segments[i][0]
            lab = c_dec.label
            # If this language only occurs once across the entire sequence and the token is <= 3 chars (never suppress English or cross script boundaries)
            if lab != "en" and sum(1 for d in smoothed if d.label == lab) == 1 and len(tok) <= 3:
                nbr_idx = i - 1 if i > 0 else (i + 1 if i < n - 1 else i)
                nbr = smoothed[nbr_idx].label
                if nbr != lab and segments[nbr_idx][1] == segments[i][1]:
                    nd = dict(c_dec.distribution)
                    nd[nbr] = 1.0
                    smoothed[i] = TokenDecision.create_with_trace(
                        nbr, f"{c_dec.decided_by}+SingleTokenNoiseSmoothing",
                        f"Isolated 1-token noise smoothed to {nbr}.",
                        c_dec.competing_predictions, nd, tok, c_dec.trace.model_predictions if c_dec.trace else {},
                        DecisionStage.CONTEXT_REFINEMENT
                    )
            elif len(tok) <= 2 and c_dec.label in ("so", "sl", "la", "eu", "eo", "cy", "ga", "is", "af", "zu", "ca"):
                if 0 < i < n - 1 and smoothed[i-1].label == smoothed[i+1].label and segments[i-1][1] == segments[i][1] == segments[i+1][1]:
                    nbr = smoothed[i-1].label
                    nd = dict(c_dec.distribution)
                    nd[nbr] = 1.0
                    smoothed[i] = TokenDecision.create_with_trace(
                        nbr, f"{c_dec.decided_by}+ShortTokenSmoothing",
                        f"Isolated short token smoothed to {nbr}.",
                        c_dec.competing_predictions, nd, tok, c_dec.trace.model_predictions if c_dec.trace else {},
                        DecisionStage.CONTEXT_REFINEMENT
                    )

        # 3. Token-level dictionary output
        token_dicts = []
        for i, dec in enumerate(smoothed):
            seg_str, sc, s_idx, e_idx = segments[i]
            token_dicts.append({
                "token": seg_str, "label": dec.label,
                "confidence": float(dec.distribution.get(dec.label, 1.0)),
                "decided_by": dec.decided_by, "reason": dec.reason,
                "start": s_idx, "end": e_idx, "script": sc
            })

        # 4. Spans merging
        spans: List[Tuple[str, str]] = []
        cur_lang, cur_start = smoothed[0].label, 0
        for i in range(1, n):
            lab = smoothed[i].label
            if lab != cur_lang:
                if not any(c.isalnum() for c in segments[i][0]):
                    smoothed[i].label = cur_lang
                    continue
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
    def __init__(self, ft_path: str = "lid.176.ftz"):
        self.fasttext = FastTextModel(ft_path=ft_path)
        self.glotlid = GlotLIDModel()
        self.lingua = LinguaModel()
        
        # Models for sentence-level discovery
        self.discovery_models = [self.fasttext, self.glotlid, self.lingua]
        # Models for token-level classification (GlotLID kept out for efficiency)
        self.token_models = [self.fasttext, self.lingua]

    def identify(self, text: str, allowed_langs: Iterable[str] = None) -> List[TokenDecision]:
        if not text or not text.strip():
            return []
        # 1. Tokenize text
        segments = Tokenizer.segment(text)
        if not segments:
            return []
        # 2. Find possible languages
        candidate_langs = (
            CandidateGenerator.get_candidates(allowed_langs)
            if allowed_langs is not None
            else CandidateDetector.detect(text, self.discovery_models, segments=segments)
        )
        # 3. Classify each token
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text)
        # 4. Resolve conflicting predictions
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text)
        # 5. Clean up results and build spans
        smoothed_decisions, _, _ = ResultRefiner.refine_and_assemble(text, segments, decisions)
        return smoothed_decisions

    def identify_to_dict(self, text: str, allowed_langs: Iterable[str] = None) -> List[Dict]:
        if not text or not text.strip():
            return []
        segments = Tokenizer.segment(text)
        if not segments:
            return []
        candidate_langs = (
            CandidateGenerator.get_candidates(allowed_langs)
            if allowed_langs is not None
            else CandidateDetector.detect(text, self.discovery_models, segments=segments)
        )
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text)
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text)
        _, _, token_dicts = ResultRefiner.refine_and_assemble(text, segments, decisions)
        return token_dicts

    def detect_languages(self, text: str, allowed_langs: Iterable[str] = None) -> List[Tuple[str, str]]:
        if not text or not text.strip():
            return [(text, "en")]
        segments = Tokenizer.segment(text)
        if not segments:
            return [(text, "en")]
        candidate_langs = (
            CandidateGenerator.get_candidates(allowed_langs)
            if allowed_langs is not None
            else CandidateDetector.detect(text, self.discovery_models, segments=segments)
        )
        token_predictions = TokenClassifier.classify_tokens(segments, candidate_langs, self.token_models, text)
        decisions = DecisionMaker.make_decisions(segments, token_predictions, candidate_langs, self.token_models, text)
        _, spans, _ = ResultRefiner.refine_and_assemble(text, segments, decisions)
        return spans


_detector = None

def get_detector(ft_path: str = "lid.176.ftz") -> PolyLIDPipeline:
    global _detector
    if _detector is None:
        _detector = PolyLIDPipeline(ft_path=ft_path)
    return _detector

def detect_languages(text: str, allowed_langs: Iterable[str] = None) -> List[Tuple[str, str]]:
    return get_detector().detect_languages(text, allowed_langs=allowed_langs)

def batch_detect_languages(texts: List[str], allowed_langs: Iterable[str] = None) -> List[List[Tuple[str, str]]]:
    det = get_detector()
    return [det.detect_languages(t, allowed_langs=allowed_langs) for t in texts]


__all__ = [
    "PolyLIDPipeline", "get_detector", "detect_languages", "batch_detect_languages",
    "Tokenizer", "CandidateDetector", "TokenClassifier", "DecisionMaker", "ResultRefiner",
    "DecisionEngine", "PredictionAnalyzer", "PredictionMerger", "ContextChecker",
    "BaseLanguageModel", "FastTextModel", "GlotLIDModel", "LinguaModel",
    "ModelPrediction", "PredictionEvidence", "TokenDecision", "DecisionTrace", "DecisionStage",
    "CandidateGenerator", "SUPPORTED_LANGS", "LANG_NAME_TO_CODE", "SCRIPT_RANGES",
    "SCRIPT_TO_DEFAULT_LANG", "SCRIPT_TO_LANGUAGES"
]

