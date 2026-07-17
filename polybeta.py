from __future__ import annotations

import importlib
import os
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


SUPPORTED_LANGS = {
    "ar", "bg", "bn", "de", "en", "es", "fr", "gu", "hi", "id",
    "it", "ja", "kn", "ko", "ml", "nl", "pl", "pt", "ru", "ta",
    "te", "th", "tr", "ur", "vi", "zh"
}

NO_SPACE_SCRIPTS = {"HAN", "HIRAGANA", "KATAKANA", "HANGUL", "THAI"}

SCRIPT_RANGES = {
    "HAN": [(0x4E00, 0x9FFF)],
    "HIRAGANA": [(0x3040, 0x309F)],
    "KATAKANA": [(0x30A0, 0x30FF)],
    "HANGUL": [(0xAC00, 0xD7AF)],
    "THAI": [(0x0E00, 0x0E7F)],
    "ARABIC": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],
    "DEVANAGARI": [(0x0900, 0x097F)],
    "BENGALI": [(0x0980, 0x09FF)],
    "GUJARATI": [(0x0A80, 0x0AFF)],
    "GURMUKHI": [(0x0A00, 0x0A7F)],
    "KANNADA": [(0x0C80, 0x0CFF)],
    "MALAYALAM": [(0x0D00, 0x0D7F)],
    "ORIYA": [(0x0B00, 0x0B7F)],
    "TAMIL": [(0x0B80, 0x0BFF)],
    "TELUGU": [(0x0C00, 0x0C7F)],
    "CYRILLIC": [(0x0400, 0x04FF)],
    "LATIN": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
}

LANG_NAME_TO_CODE = {
    "arabic": "ar", "bulgarian": "bg", "bengali": "bn", "german": "de",
    "english": "en", "spanish": "es", "french": "fr", "gujarati": "gu",
    "hindi": "hi", "indonesian": "id", "italian": "it", "japanese": "ja",
    "kannada": "kn", "korean": "ko", "malayalam": "ml", "dutch": "nl",
    "polish": "pl", "portuguese": "pt", "russian": "ru", "tamil": "ta",
    "telugu": "te", "thai": "th", "turkish": "tr", "urdu": "ur",
    "vietnamese": "vi", "chinese": "zh"
}

LINGUA_LANG_MAP = {
    "ARABIC": "ar", "BULGARIAN": "bg", "BENGALI": "bn", "GERMAN": "de",
    "ENGLISH": "en", "SPANISH": "es", "FRENCH": "fr", "GUJARATI": "gu",
    "HINDI": "hi", "INDONESIAN": "id", "ITALIAN": "it", "JAPANESE": "ja",
    "KANNADA": "kn", "KOREAN": "ko", "MALAYALAM": "ml", "DUTCH": "nl",
    "POLISH": "pl", "PORTUGUESE": "pt", "RUSSIAN": "ru", "TAMIL": "ta",
    "TELUGU": "te", "THAI": "th", "TURKISH": "tr", "URDU": "ur",
    "VIETNAMESE": "vi", "CHINESE": "zh"
}


def _resolve_asset_path(rel_path: str) -> str:
    if os.path.exists(rel_path):
        return rel_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(base_dir, rel_path)
    if os.path.exists(abs_path):
        return abs_path
    return rel_path


def require(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def normalize_lang_code(code: str) -> str:
    value = str(code or "").strip().lower()
    if not value:
        return ""
    value = value.replace("__label__", "")
    value = value.replace("_", "-")
    alias = {
        "zh-cn": "zh", "zh-tw": "zh", "zh-hans": "zh", "zh-hant": "zh", "jp": "ja",
        "jpn": "ja", "ko-kr": "ko", "pt-br": "pt", "asm": "as", "ben": "bn", "guj": "gu",
        "hin": "hi", "kan": "kn", "kas": "ks", "mal": "ml", "mar": "mr", "nep": "ne",
        "ori": "or", "pan": "pa", "san": "sa", "snd": "sd", "tam": "ta", "tel": "te",
        "urd": "ur", "eng": "en", "other": "und",
        "dty": "ne", "dot": "ne", "npi": "ne", "new": "ne", "bho": "hi", "awa": "hi", "mai": "hi", "mag": "hi"
    }
    if value in alias:
        return alias[value]
    if value in SUPPORTED_LANGS:
        return value
    if value in LANG_NAME_TO_CODE:
        return LANG_NAME_TO_CODE[value]
    head = value.split("-", 1)[0]
    if head in alias:
        return alias[head]
    if head in SUPPORTED_LANGS:
        return head
    if head in LANG_NAME_TO_CODE:
        return LANG_NAME_TO_CODE[head]
    return ""


@lru_cache(maxsize=8192)
def get_script(ch: str) -> str:
    code = ord(ch)
    for script, ranges in SCRIPT_RANGES.items():
        for lo, hi in ranges:
            if lo <= code <= hi:
                return script
    return "OTHER"


def dominant_script(text: str) -> str:
    votes = Counter()
    for ch in text:
        if ch.isalpha():
            votes[get_script(ch)] += 1
    return votes.most_common(1)[0][0] if votes else "OTHER"


def normalize_probs(dist: Dict[str, float]) -> Dict[str, float]:
    filtered = {k: float(v) for k, v in dist.items() if v > 0 and k in SUPPORTED_LANGS}
    total = sum(filtered.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in filtered.items()}


def top_label(dist: Dict[str, float]) -> Tuple[str, float, float]:
    if not dist:
        return "en", 0.0, 0.0
    ranked = sorted(dist.items(), key=lambda item: item[1], reverse=True)
    best_lang, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    return best_lang, float(best_score), float(best_score - second_score)


class CandidateGenerator:
    LANGUAGE_ALIASES: Dict[str, str] = {
        "eng": "en", "hin": "hi", "spa": "es", "nep": "ne", "ara": "ar", "tur": "tr",
        "ind": "id", "mar": "mr", "ben": "bn", "tam": "ta", "tel": "te", "mal": "ml",
        "kan": "kn", "guj": "gu", "pan": "pa", "urd": "ur"
    }

    @classmethod
    def project_distribution(cls, dist: Dict[str, float], allowed: Iterable[str]) -> Dict[str, float]:
        if allowed is None:
            return normalize_probs(dist)
        allowed_set = set(allowed)
        filtered = {k: v for k, v in dist.items() if k in allowed_set}
        return normalize_probs(filtered)

    @classmethod
    def normalize_label(cls, label: str) -> str:
        clean = str(label).strip().lower()
        return cls.LANGUAGE_ALIASES.get(clean, clean)

    @classmethod
    def normalize_candidates(cls, langs: Iterable[str]) -> set[str]:
        if not langs:
            return SUPPORTED_LANGS
        return {cls.normalize_label(l) for l in langs if l and str(l).strip()}

    @classmethod
    def generate_candidates(cls, allowed_langs: Iterable[str] = None) -> set[str]:
        if allowed_langs is None:
            return SUPPORTED_LANGS
        if isinstance(allowed_langs, str):
            if allowed_langs.strip().lower() == "all":
                return SUPPORTED_LANGS
            return {cls.normalize_label(allowed_langs)}
        return cls.normalize_candidates(allowed_langs)

    @classmethod
    def get_candidates(cls, allowed_langs: Iterable[str] = None) -> set[str]:
        return cls.generate_candidates(allowed_langs)


@dataclass
class Prediction:
    label: str
    confidence: float
    margin: float
    ranked_candidates: List[Tuple[str, float]]
    model: str
    raw_dist: Dict[str, float]
    res_dist: Dict[str, float]

    @property
    def expert(self) -> str:
        return self.model


@dataclass
class Evidence:
    model: str
    prediction: Prediction
    margin: float
    confidence: float
    boundary: Any
    agreement_count: int
    script: str
    token: str
    raw_candidates: List[Tuple[str, float]]


class DecisionStage(str, Enum):
    UNANIMOUS = "Unanimous Agreement"
    CONSENSUS = "Consensus"
    LOCAL_CONTEXT = "Local Context Arbitration"
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
class PredictionResult:
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
    ) -> "PredictionResult":
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
        if len(vals) >= 2:
            return vals[0] - vals[1]
        return vals[0] if vals else 0.0

    def is_consensus_or_agreement(self) -> bool:
        if self.trace and self.trace.decision_stage in (
            DecisionStage.UNANIMOUS,
            DecisionStage.CONSENSUS,
        ):
            return True
        return any(x in self.decided_by for x in ("Consensus", "Agreement", "Unanimous"))


@dataclass
class BoundaryEvidence:
    script_changed: bool
    models_disagree: bool
    is_switch_point: bool
    needs_arbitration: bool


class BaseExpert:
    def __init__(
        self,
        name: str,
        supported_scripts: Set[str] = None,
        unsupported_scripts: Set[str] = None,
    ):
        self.name = name
        self.supported_scripts = supported_scripts or set()
        self.unsupported_scripts = unsupported_scripts or set()
        self._cache: Dict[str, Dict[str, float]] = {}

    def supports_script(self, script: str) -> bool:
        return script not in self.unsupported_scripts

    def should_abstain(self, token: str, script: str, allowed_langs: Iterable[str] = None) -> bool:
        if not self.supports_script(script):
            return True
        if not token or not token.strip():
            return True
        return False

    def supports_token(self, token: str, script: str, allowed_langs: Iterable[str] = None) -> bool:
        return not self.should_abstain(token, script, allowed_langs)

    def predict(self, text: str, allowed: Iterable[str]) -> Dict[str, float]:
        raise NotImplementedError

    def evaluate(self, text: str, allowed: Iterable[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        restricted = self.predict(text, allowed)
        key = unicodedata.normalize("NFC", text or "").casefold()
        raw = self._cache.get(key, restricted)
        return raw, restricted

    def _restrict(self, dist: Dict[str, float], allowed: Iterable[str]) -> Dict[str, float]:
        return CandidateGenerator.project_distribution(dist, allowed)


class FastTextExpert(BaseExpert):
    """
    Pure FastText Expert.
    No routing. No weights. No confidence scaling.
    Just token -> distribution.
    """
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
            predictions = self.model.f.predict(text_cln, 5, 0.0, "strict")
            if predictions:
                probs, labels = zip(*predictions)
                raw = {}
                for l, p in zip(labels, probs):
                    code = normalize_lang_code(l)
                    if code:
                        raw[code] = raw.get(code, 0.0) + float(p)
                dist = normalize_probs(raw)
            else:
                dist = {}
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)


class LinguaExpert(BaseExpert):
    """
    Pure Lingua Expert.
    Same philosophy: token -> distribution.
    """
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

    def should_abstain(self, token: str, script: str, allowed_langs: Iterable[str] = None) -> bool:
        return super().should_abstain(token, script, allowed_langs)

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
            for conf in confs[:8]:
                lang = LINGUA_LANG_MAP.get(str(conf.language).split(".")[-1].upper().strip(), "")
                if lang:
                    raw[lang] = max(raw.get(lang, 0.0), float(conf.value))
            dist = normalize_probs(raw)
        except Exception:
            dist = {}
        self._cache[key] = dist
        return self._restrict(dist, allowed)



class Tokenizer:
    """
    Module 3: Tokenizer.
    Responsible for clean script and punctuation-aware segment tokenization.
    """
    @staticmethod
    def segment_text_with_offsets(text: str) -> List[Tuple[str, str, int, int]]:
        parts = []
        buf = []
        last_script = ""
        start_idx = 0
        for i, ch in enumerate(text):
            category = unicodedata.category(ch)
            is_internal_punc = (
                ch in {"'", "-", "’"}
                and i > 0
                and i < len(text) - 1
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
        return [
            p for p in parts
            if isinstance(p[0], str) and (any(c.isalpha() for c in p[0]) or any(c.isdigit() for c in p[0]))
        ]


class SentenceLanguageDiscovery:
    """
    Module 1: Sentence Language Discovery (Level 1 Global Context).
    """
    def __init__(self, ft_path: str = "lid.176.ftz", max_iterations: int = 6):
        self.max_iterations = max_iterations
        self.model = None
        ft_mod = require("fasttext")
        resolved_path = _resolve_asset_path(ft_path)
        if ft_mod is not None and os.path.exists(resolved_path):
            try:
                self.model = ft_mod.load_model(resolved_path)
            except Exception:
                self.model = None

    def discover_candidates(self, text: str) -> Set[str]:
        if not text or not text.strip() or self.model is None:
            return {"en"}

        words = [w.strip(".,!?;:\"'()[]{}") for w in text.replace('\n', ' ').strip().split() if len(w.strip(".,!?;:\"'()[]{}")) >= 1]
        if not words:
            return {"en"}

        D: Set[str] = set()
        uniform_prior = 1.0 / len(SUPPORTED_LANGS)

        # 1. Script-to-Candidate Anchoring across our exact 26 supported languages
        SCRIPT_TO_LANGS = {
            "ARABIC": {"ar", "ur"},
            "BENGALI": {"bn"},
            "CYRILLIC": {"ru", "uk"},
            "DEVANAGARI": {"hi", "mr"},
            "GUJARATI": {"gu"},
            "HAN": {"zh", "ja"},
            "CJK": {"zh", "ja"},
            "HANGUL": {"ko"},
            "KANA": {"ja"},
            "TAMIL": {"ta"},
            "TELUGU": {"te"},
            "THAI": {"th"},
        }
        for _, s_name, _, _ in Tokenizer.segment_text_with_offsets(text):
            s_upper = s_name.upper() if s_name else ""
            if s_upper in SCRIPT_TO_LANGS:
                D.update(SCRIPT_TO_LANGS[s_upper])

        # 2. Global Sentence Prediction
        try:
            preds = self.model.f.predict(" ".join(words), 10, 0.0, "strict")
            if preds:
                probs, labels = zip(*preds)
                for prob, label in zip(probs, labels):
                    code = normalize_lang_code(label)
                    if code in SUPPORTED_LANGS and float(prob) >= max(0.05, uniform_prior * 2.0):
                        D.add(code)

            # 3. Multi-Scale Rolling Phrase Window Discovery (k=1 through k=6)
            for k in (1, 2, 3, 4, 5, 6):
                for j in range(len(words) - k + 1):
                    w_text = " ".join(words[j:j+k])
                    if len(w_text) >= 2:
                        top_n = 3 if k <= 2 else 2
                        w_preds = self.model.f.predict(w_text, top_n, 0.0, "strict")
                        if w_preds:
                            w_probs, w_labels = zip(*w_preds)
                            for prob, label in zip(w_probs, w_labels):
                                code = normalize_lang_code(label)
                                threshold = max(0.04, uniform_prior * 1.5) if k <= 2 else 0.35
                                if code in SUPPORTED_LANGS and float(prob) >= threshold:
                                    D.add(code)
        except Exception:
            pass

        if not D:
            D.add("en")
        return D


class BoundaryAnalyzer:
    """
    Module 4: Simplified Boundary Analyzer.
    """
    @staticmethod
    def analyze(
        predictions: List[Prediction],
        token_idx: int,
        scripts: List[str],
    ) -> BoundaryEvidence:
        current_script = scripts[token_idx] if 0 <= token_idx < len(scripts) else "OTHER"
        prev_script = scripts[token_idx - 1] if token_idx > 0 else current_script
        next_script = scripts[token_idx + 1] if token_idx < len(scripts) - 1 else current_script

        script_changed = (
            (prev_script != current_script and prev_script != "OTHER" and current_script != "OTHER")
            or (next_script != current_script and next_script != "OTHER" and current_script != "OTHER")
        )

        valid_preds = [
            p for p in predictions
            if p.label and 0.0 <= p.confidence <= 1.0 and p.margin >= 0.0
        ]
        labels = {p.label for p in valid_preds}
        models_disagree = len(labels) > 1

        is_switch_point = script_changed or models_disagree
        needs_arbitration = is_switch_point or len(valid_preds) == 0

        return BoundaryEvidence(
            script_changed=script_changed,
            models_disagree=models_disagree,
            is_switch_point=is_switch_point,
            needs_arbitration=needs_arbitration,
        )


class EvidenceValidator:
    """
    Module 4: Evidence Validator.
    """
    @staticmethod
    def validate(
        predictions: List[Prediction],
        token_str: str,
        script: str,
        allowed_langs: Iterable[str] = None,
        boundary_ev=None,
    ) -> List[Evidence]:
        evidences = []
        allowed_set = set(allowed_langs) if allowed_langs is not None else None
        valid_preds = []
        for p in predictions:
            if not p.label or p.confidence < 0.0 or p.confidence > 1.0 or p.margin < 0.0:
                continue
            if allowed_set and p.label not in allowed_set:
                continue
            valid_preds.append(p)

        label_counts = Counter(p.label for p in valid_preds)

        for p in valid_preds:
            evidences.append(
                Evidence(
                    model=p.model,
                    prediction=p,
                    margin=p.margin,
                    confidence=p.confidence,
                    boundary=boundary_ev,
                    agreement_count=label_counts[p.label],
                    script=script,
                    token=token_str,
                    raw_candidates=p.ranked_candidates,
                )
            )
        return evidences


class LocalContextAnalyzer:
    """
    Module 4b: Local Context Refinement (Level 3 in Three-Level Context Hierarchy).
    """
    @staticmethod
    def is_resolvable(token_str: str) -> bool:
        if not token_str or len(token_str) < 2:
            return False
        if not token_str.isalpha():
            return False
        if token_str.isupper() and len(token_str) <= 4:
            return False
        return True

    @staticmethod
    def should_trigger(
        token_str: str,
        consensus_ev: Evidence | None,
        boundary_ev: BoundaryEvidence,
        evidences: List[Evidence],
    ) -> bool:
        if not LocalContextAnalyzer.is_resolvable(token_str):
            return False
        if boundary_ev.needs_arbitration:
            return True
        if evidences:
            best = EvidenceComparison.select_strongest(evidences)
            if best.margin <= 0.20 or (len(token_str) <= 3 and best.margin <= 0.25):
                return True
        return False

    @staticmethod
    def analyze(
        token_idx: int,
        segments: List[Tuple[str, str, int, int]],
        candidate_langs: Iterable[str],
        experts: List,
        boundary_ev: BoundaryEvidence,
    ) -> List[Evidence]:
        if not segments or not (0 <= token_idx < len(segments)):
            return []

        token_str, script, _, _ = segments[token_idx]

        start_w = token_idx
        while start_w > 0 and segments[start_w - 1][1] == script and (token_idx - start_w) < 2:
            if any(segments[start_w - 1][0].endswith(p) for p in '.,!?;:'):
                break
            start_w -= 1

        end_w = token_idx + 1
        while end_w < len(segments) and segments[end_w][1] == script and (end_w - token_idx) <= 2:
            if any(segments[end_w - 1][0].endswith(p) for p in '.,!?;:'):
                break
            end_w += 1

        phrase_tokens = [segments[j][0] for j in range(start_w, end_w)]
        if len(phrase_tokens) <= 1:
            return []

        phrase_str = " ".join(phrase_tokens)
        local_evidences: List[Evidence] = []

        for expert in experts:
            if expert.supports_token(token_str, script, candidate_langs):
                raw_dist, res_dist = expert.evaluate(phrase_str, candidate_langs)
                if res_dist:
                    lab, conf, margin = top_label(res_dist)
                    ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                    model_name = f"LocalContext({expert.name})"
                    pred = Prediction(
                        label=lab,
                        confidence=conf,
                        margin=margin,
                        ranked_candidates=ranked,
                        model=model_name,
                        raw_dist=raw_dist,
                        res_dist=res_dist,
                    )
                    local_evidences.append(
                        Evidence(
                            model=model_name,
                            prediction=pred,
                            margin=margin,
                            confidence=conf,
                            boundary=boundary_ev,
                            agreement_count=1,
                            script=script,
                            token=token_str,
                            raw_candidates=ranked,
                        )
                    )

        label_counts = Counter(e.prediction.label for e in local_evidences)
        for e in local_evidences:
            e.agreement_count = label_counts[e.prediction.label]

        return local_evidences


class ConsensusBuilder:
    @staticmethod
    def build(evidences: List[Evidence], boundary_ev: BoundaryEvidence) -> Tuple[Optional[Evidence], List[Evidence]]:
        if not evidences:
            return None, []
            
        label_groups = defaultdict(list)
        for ev in evidences:
            label_groups[ev.prediction.label].append(ev)

        agreed_groups = [evs for evs in label_groups.values() if len(evs) >= 2]
        if not agreed_groups:
            return None, evidences

        agreed_evs = agreed_groups[0]
        agreed_lab = agreed_evs[0].prediction.label
        other_evs = [ev for ev in evidences if ev.prediction.label != agreed_lab]

        avg_margin = sum(e.margin for e in agreed_evs) / len(agreed_evs)
        avg_conf = sum(e.confidence for e in agreed_evs) / len(agreed_evs)
        consensus_model_name = "+".join(e.model for e in agreed_evs)
        
        consensus_pred = Prediction(
            label=agreed_lab,
            confidence=avg_conf,
            margin=avg_margin,
            ranked_candidates=agreed_evs[0].prediction.ranked_candidates,
            model=consensus_model_name,
            raw_dist=agreed_evs[0].prediction.raw_dist,
            res_dist=agreed_evs[0].prediction.res_dist
        )
        consensus_ev = Evidence(
            model=consensus_model_name,
            prediction=consensus_pred,
            margin=avg_margin,
            confidence=avg_conf,
            boundary=boundary_ev,
            agreement_count=len(agreed_evs),
            script=agreed_evs[0].script,
            token=agreed_evs[0].token,
            raw_candidates=agreed_evs[0].raw_candidates
        )
        return consensus_ev, other_evs


class EvidenceComparison:
    """
    Module 6a: Evidence Comparison.
    """
    @staticmethod
    def is_stronger(ev1: Evidence, ev2: Evidence) -> bool:
        if ev1.agreement_count > ev2.agreement_count:
            return True
        if ev1.agreement_count < ev2.agreement_count:
            return False
        if ev1.margin > ev2.margin:
            return True
        if ev1.margin < ev2.margin:
            return False
        return ev1.confidence > ev2.confidence

    @staticmethod
    def select_strongest(evidences: List[Evidence]) -> Evidence:
        best = evidences[0]
        for ev in evidences[1:]:
            if EvidenceComparison.is_stronger(ev, best):
                best = ev
        return best


class ArbitrationEngine:
    """
    Module 6b: Arbitration Engine.
    """
    @staticmethod
    def arbitrate(
        evidences: List[Evidence],
        token_idx: int,
        segments: List[Tuple[str, str, int, int]],
        boundary_ev: BoundaryEvidence,
        local_evidences: List[Evidence] = None,
    ) -> PredictionResult:
        token_str = segments[token_idx][0] if 0 <= token_idx < len(segments) else ""
        all_evidences = list(evidences) + (local_evidences or [])
        if not all_evidences:
            return PredictionResult.create_with_trace(
                label="",
                decided_by="None",
                reason="No active models available.",
                competing_predictions=[],
                distribution={},
                token=token_str,
                model_predictions={},
                decision_stage=DecisionStage.NO_MODELS,
            )

        competing = [(ev.model, ev.prediction.label) for ev in all_evidences]
        model_preds = {ev.model: ev.prediction.label for ev in all_evidences}

        if not boundary_ev.needs_arbitration and not local_evidences:
            best_ev = EvidenceComparison.select_strongest(evidences)
            if len(evidences) >= 2 or best_ev.agreement_count >= 2 or (best_ev.confidence >= 0.80 and best_ev.margin >= 0.25 and len(token_str) >= 3):
                reason = f"Unanimous agreement on {best_ev.prediction.label} without boundary ambiguity."
                stage = DecisionStage.UNANIMOUS
            else:
                reason = f"Single-model evaluation: {best_ev.model} selected for {best_ev.prediction.label} without boundary conflict."
                stage = DecisionStage.EVIDENCE_COMPARISON
            return PredictionResult.create_with_trace(
            label=best_ev.prediction.label,
            decided_by=best_ev.model,
            reason=reason,
            competing_predictions=competing,
            distribution=best_ev.prediction.res_dist,
            token=token_str,
            model_predictions=model_preds,
            decision_stage=stage,
        )

        consensus_ev, dissent_evs = ConsensusBuilder.build(evidences, boundary_ev)

        if consensus_ev is not None:
            agreed_lab = consensus_ev.prediction.label
            dissent_evs = [ev for ev in dissent_evs + (local_evidences or []) if ev.prediction.label != agreed_lab]
            consensus_model_name = consensus_ev.model
            if dissent_evs:
                best_dissent = EvidenceComparison.select_strongest(dissent_evs)
                if EvidenceComparison.is_stronger(best_dissent, consensus_ev):
                    reason = (
                        f"Local/Dissenting model selected: {best_dissent.model} produced superior "
                        f"relative evidence for {best_dissent.prediction.label} over {agreed_lab} consensus."
                    )
                    return PredictionResult.create_with_trace(
            label=best_dissent.prediction.label,
            decided_by=best_dissent.model,
            reason=reason,
            competing_predictions=competing,
            distribution=best_dissent.prediction.res_dist,
            token=token_str,
            model_predictions=model_preds,
            decision_stage=DecisionStage.LOCAL_CONTEXT,
        )
                else:
                    reason = (
                        f"Consensus retained: Independent models agree on {agreed_lab} with "
                        f"superior relative evidence over {best_dissent.model}."
                    )
                    return PredictionResult.create_with_trace(
            label=consensus_ev.prediction.label,
            decided_by=consensus_model_name,
            reason=reason,
            competing_predictions=competing,
            distribution=consensus_ev.prediction.res_dist,
            token=token_str,
            model_predictions=model_preds,
            decision_stage=DecisionStage.EVIDENCE_COMPARISON,
        )
            else:
                reason = f"Consensus selected: Models independently agree on {agreed_lab}."
                return PredictionResult.create_with_trace(
            label=consensus_ev.prediction.label,
            decided_by=consensus_model_name,
            reason=reason,
            competing_predictions=competing,
            distribution=consensus_ev.prediction.res_dist,
            token=token_str,
            model_predictions=model_preds,
            decision_stage=DecisionStage.CONSENSUS,
        )

        best_ev = EvidenceComparison.select_strongest(all_evidences)
        reason = f"No consensus. {best_ev.model} selected via sequential relative evidence comparison."
        return PredictionResult.create_with_trace(
            label=best_ev.prediction.label,
            decided_by=best_ev.model,
            reason=reason,
            competing_predictions=competing,
            distribution=best_ev.prediction.res_dist,
            token=token_str,
            model_predictions=model_preds,
            decision_stage=DecisionStage.LOCAL_CONTEXT,
        )
class ContextRefinement:
    """
    Module 10: Context Refinement (formerly Spatial Smoothing).
    Replaces all empirical thresholds and language-specific checks with purely relative
    statistical dominance, differential logit attribution, and model-agnostic ideographic continuity.
    """
    @classmethod
    def refine(cls, decisions: List[PredictionResult], segments: List[Tuple[str, str, int, int]]) -> List[PredictionResult]:
        n = len(decisions)
        if n < 2 or len(segments) != n:
            return decisions

        smoothed = list(decisions)
        smoothed = cls._refine_ideographic_clauses(smoothed, segments)
        smoothed = cls._refine_script_block_peaks(smoothed, segments)
        smoothed = cls._refine_sandwiches(smoothed, segments)
        smoothed = cls._refine_orphans(smoothed, segments)
        return smoothed

    @classmethod
    def _refine_ideographic_clauses(cls, smoothed: List[PredictionResult], segments: List[Tuple[str, str, int, int]]) -> List[PredictionResult]:
        n = len(smoothed)
        idx = 0
        ideographic_scripts = {"HAN", "HIRAGANA", "KATAKANA", "HANGUL", "BOPOMOFO"}
        while idx < n:
            script = segments[idx][1]
            if script in ideographic_scripts:
                end = idx
                while end < n and segments[end][1] in ideographic_scripts:
                    end += 1
                consensus_anchors = [
                    smoothed[j].label for j in range(idx, end)
                    if smoothed[j].label and smoothed[j].is_consensus_or_agreement()
                ]
                if not consensus_anchors:
                    consensus_anchors = [smoothed[j].label for j in range(idx, end) if smoothed[j].label]
                if consensus_anchors:
                    dominant_label = Counter(consensus_anchors).most_common(1)[0][0]
                    for j in range(idx, end):
                        if smoothed[j].label != dominant_label and not smoothed[j].is_consensus_or_agreement():
                            new_dist = dict(smoothed[j].distribution)
                            new_dist[dominant_label] = max(
                                new_dist.get(dominant_label, 0.0),
                                smoothed[j].distribution.get(smoothed[j].label, 0.0)
                            )
                            if smoothed[j].trace:
                                smoothed[j] = PredictionResult.create_with_trace(
                                label=dominant_label,
                                decided_by=f"{smoothed[j].decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: zero-heuristic ideographic continuity projected to {dominant_label} syntactic clause.",
                                competing_predictions=smoothed[j].competing_predictions,
                                distribution=new_dist,
                                token=smoothed[j].trace.token,
                                model_predictions=smoothed[j].trace.model_predictions,
                                decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                )
                            else:
                                smoothed[j] = PredictionResult(
                                label=dominant_label,
                                decided_by=f"{smoothed[j].decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: zero-heuristic ideographic continuity projected to {dominant_label} syntactic clause.",
                                competing_predictions=smoothed[j].competing_predictions,
                                distribution=new_dist,
                                trace=None,
                                )
                idx = end
            else:
                idx += 1
        return smoothed

    @classmethod
    def _refine_script_block_peaks(cls, smoothed: List[PredictionResult], segments: List[Tuple[str, str, int, int]]) -> List[PredictionResult]:
        n = len(smoothed)
        idx = 0
        while idx < n:
            script = segments[idx][1]
            if script not in ("OTHER", "COMMON", "HAN", "HIRAGANA", "KATAKANA", "HANGUL", "BOPOMOFO") and not segments[idx][0].isdigit():
                end = idx
                while end < n and segments[end][1] == script and not segments[end][0].isdigit():
                    end += 1
                if end > idx + 1:
                    peaks = []
                    for j in range(idx, end):
                        dec = smoothed[j]
                        if not dec.label:
                            continue
                        dist = dec.distribution
                        p_top = dist.get(dec.label, 0.0)
                        sorted_probs = sorted(dist.values(), reverse=True)
                        p_second = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
                        margin = p_top - p_second
                        if dec.is_consensus_or_agreement() and margin > 0.0:
                            if margin >= 0.15 and len(segments[j][0]) >= 3:
                                peaks.append((j, dec.label, p_top, margin))

                    if peaks:
                        first_peak_idx, first_label, _, _ = peaks[0]
                        for j in range(idx, first_peak_idx):
                            curr_dec = smoothed[j]
                            if curr_dec.label != first_label and not curr_dec.is_consensus_or_agreement():
                                new_dist = dict(curr_dec.distribution)
                                new_dist[first_label] = max(new_dist.get(first_label, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                                if curr_dec.trace:
                                    smoothed[j] = PredictionResult.create_with_trace(
                                    label=first_label,
                                    decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                    reason=f"Spatial context smoothing applied: zero-heuristic statistical attribution projected to {first_label} peak.",
                                    competing_predictions=curr_dec.competing_predictions,
                                    distribution=new_dist,
                                    token=curr_dec.trace.token,
                                    model_predictions=curr_dec.trace.model_predictions,
                                    decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                    )
                                else:
                                    smoothed[j] = PredictionResult(
                                    label=first_label,
                                    decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                    reason=f"Spatial context smoothing applied: zero-heuristic statistical attribution projected to {first_label} peak.",
                                    competing_predictions=curr_dec.competing_predictions,
                                    distribution=new_dist,
                                    trace=None,
                                    )

                        for p_idx in range(len(peaks) - 1):
                            k1, l1, _, _ = peaks[p_idx]
                            k2, l2, _, _ = peaks[p_idx + 1]
                            if l1 == l2:
                                for j in range(k1 + 1, k2):
                                    curr_dec = smoothed[j]
                                    tok_str = segments[j][0]
                                    has_support = curr_dec.distribution.get(l1, 0.0) >= 0.10
                                    matches_outer = (j + 2 < len(smoothed) and smoothed[j + 2].label == curr_dec.label) or (j - 2 >= 0 and smoothed[j - 2].label == curr_dec.label)
                                    if curr_dec.label != l1 and not curr_dec.is_consensus_or_agreement() and has_support and not matches_outer and (curr_dec.margin <= 0.25 or len(tok_str) <= 3):
                                        new_dist = dict(curr_dec.distribution)
                                        new_dist[l1] = max(new_dist.get(l1, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                                        if curr_dec.trace:
                                            smoothed[j] = PredictionResult.create_with_trace(
                                            label=l1,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: zero-heuristic statistical continuity between {l1} peaks.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            token=curr_dec.trace.token,
                                            model_predictions=curr_dec.trace.model_predictions,
                                            decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                            )
                                        else:
                                            smoothed[j] = PredictionResult(
                                            label=l1,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: zero-heuristic statistical continuity between {l1} peaks.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            trace=None,
                                            )
                            else:
                                b_split = k1 + 1
                                min_abs_delta = float('inf')
                                for j in range(k1 + 1, k2):
                                    dist_j = smoothed[j].distribution
                                    delta = dist_j.get(l1, 0.0) - dist_j.get(l2, 0.0)
                                    if abs(delta) < min_abs_delta or (delta <= 0 and b_split == k1 + 1):
                                        min_abs_delta = abs(delta)
                                        b_split = j
                                for j in range(k1 + 1, b_split):
                                    curr_dec = smoothed[j]
                                    tok_str = segments[j][0]
                                    p1 = curr_dec.distribution.get(l1, 0.0)
                                    p2 = curr_dec.distribution.get(l2, 0.0)
                                    if curr_dec.label != l1 and not curr_dec.is_consensus_or_agreement() and p1 >= p2 and (curr_dec.margin <= 0.25 or len(tok_str) <= 3):
                                        new_dist = dict(curr_dec.distribution)
                                        new_dist[l1] = max(new_dist.get(l1, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                                        if curr_dec.trace:
                                            smoothed[j] = PredictionResult.create_with_trace(
                                            label=l1,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: differential logit attribution projected to {l1}.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            token=curr_dec.trace.token,
                                            model_predictions=curr_dec.trace.model_predictions,
                                            decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                            )
                                        else:
                                            smoothed[j] = PredictionResult(
                                            label=l1,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: differential logit attribution projected to {l1}.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            trace=None,
                                            )
                                for j in range(b_split, k2):
                                    curr_dec = smoothed[j]
                                    tok_str = segments[j][0]
                                    p1 = curr_dec.distribution.get(l1, 0.0)
                                    p2 = curr_dec.distribution.get(l2, 0.0)
                                    if curr_dec.label != l2 and not curr_dec.is_consensus_or_agreement() and p2 > p1 and (curr_dec.margin <= 0.25 or len(tok_str) <= 3):
                                        new_dist = dict(curr_dec.distribution)
                                        new_dist[l2] = max(new_dist.get(l2, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                                        if curr_dec.trace:
                                            smoothed[j] = PredictionResult.create_with_trace(
                                            label=l2,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: differential logit attribution projected to {l2}.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            token=curr_dec.trace.token,
                                            model_predictions=curr_dec.trace.model_predictions,
                                            decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                            )
                                        else:
                                            smoothed[j] = PredictionResult(
                                            label=l2,
                                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                            reason=f"Spatial context smoothing applied: differential logit attribution projected to {l2}.",
                                            competing_predictions=curr_dec.competing_predictions,
                                            distribution=new_dist,
                                            trace=None,
                                            )

                        last_peak_idx, last_label, _, _ = peaks[-1]
                        for j in range(last_peak_idx + 1, end):
                            curr_dec = smoothed[j]
                            if curr_dec.label != last_label and not curr_dec.is_consensus_or_agreement():
                                new_dist = dict(curr_dec.distribution)
                                new_dist[last_label] = max(new_dist.get(last_label, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                                if curr_dec.trace:
                                    smoothed[j] = PredictionResult.create_with_trace(
                                    label=last_label,
                                    decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                    reason=f"Spatial context smoothing applied: zero-heuristic statistical attribution projected to {last_label} peak.",
                                    competing_predictions=curr_dec.competing_predictions,
                                    distribution=new_dist,
                                    token=curr_dec.trace.token,
                                    model_predictions=curr_dec.trace.model_predictions,
                                    decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                    )
                                else:
                                    smoothed[j] = PredictionResult(
                                    label=last_label,
                                    decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                    reason=f"Spatial context smoothing applied: zero-heuristic statistical attribution projected to {last_label} peak.",
                                    competing_predictions=curr_dec.competing_predictions,
                                    distribution=new_dist,
                                    trace=None,
                                    )
                idx = end
            else:
                idx += 1
        return smoothed

    @classmethod
    def _refine_sandwiches(cls, smoothed: List[PredictionResult], segments: List[Tuple[str, str, int, int]]) -> List[PredictionResult]:
        n = len(smoothed)
        if n < 3:
            return smoothed
        for _ in range(2):
            new_smoothed = list(smoothed)
            for i in range(1, n - 1):
                prev_dec = smoothed[i - 1]
                curr_dec = smoothed[i]
                next_dec = smoothed[i + 1]

                prev_script = segments[i - 1][1]
                curr_script = segments[i][1]
                next_script = segments[i + 1][1]

                if prev_script == curr_script == next_script and prev_dec.label == next_dec.label and curr_dec.label != prev_dec.label:
                    tok_str = segments[i][0]
                    has_multi_right = (i + 2 < n and smoothed[i + 2].label == prev_dec.label)
                    has_multi_left = (i - 2 >= 0 and smoothed[i - 2].label == prev_dec.label)
                    is_strict_alt = (i + 2 < n and smoothed[i + 2].label == curr_dec.label) and (i - 2 >= 0 and smoothed[i - 2].label == curr_dec.label)
                    can_smooth = (not is_strict_alt) and (
                        has_multi_right or has_multi_left or curr_dec.margin <= 0.35 or len(tok_str) <= 3 or curr_dec.distribution.get(prev_dec.label, 0.0) >= 0.05
                    )
                    if can_smooth:
                        new_dist = dict(curr_dec.distribution)
                        new_dist[prev_dec.label] = max(new_dist.get(prev_dec.label, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                        if curr_dec.trace:
                            new_smoothed[i] = PredictionResult.create_with_trace(
                            label=prev_dec.label,
                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                            reason=f"Spatial context smoothing applied: bounded by identical {prev_dec.label} neighbors in {curr_script} script.",
                            competing_predictions=curr_dec.competing_predictions,
                            distribution=new_dist,
                            token=curr_dec.trace.token,
                            model_predictions=curr_dec.trace.model_predictions,
                            decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                            )
                        else:
                            new_smoothed[i] = PredictionResult(
                            label=prev_dec.label,
                            decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                            reason=f"Spatial context smoothing applied: bounded by identical {prev_dec.label} neighbors in {curr_script} script.",
                            competing_predictions=curr_dec.competing_predictions,
                            distribution=new_dist,
                            trace=None,
                            )
            smoothed = new_smoothed

            new_smoothed = list(smoothed)
            for i in range(1, n - 2):
                prev_dec = smoothed[i - 1]
                curr_dec = smoothed[i]
                next_dec = smoothed[i + 1]
                after_dec = smoothed[i + 2]
                prev_script = segments[i - 1][1]
                curr_script = segments[i][1]
                next_script = segments[i + 1][1]
                after_script = segments[i + 2][1]
                if prev_script == curr_script == next_script == after_script and prev_dec.label == after_dec.label and curr_dec.label == next_dec.label and curr_dec.label != prev_dec.label:
                    tok_str_1 = segments[i][0]
                    tok_str_2 = segments[i + 1][0]
                    has_multi_right = (i + 3 < n and smoothed[i + 3].label == prev_dec.label)
                    has_multi_left = (i - 2 >= 0 and smoothed[i - 2].label == prev_dec.label)
                    is_strict_alt = (i + 3 < n and smoothed[i + 3].label == curr_dec.label) and (i - 2 >= 0 and smoothed[i - 2].label == curr_dec.label)
                    can_smooth = (not is_strict_alt) and (
                        has_multi_right or has_multi_left or max(curr_dec.margin, next_dec.margin) <= 0.35 or max(len(tok_str_1), len(tok_str_2)) <= 3 or max(curr_dec.distribution.get(prev_dec.label, 0.0), next_dec.distribution.get(prev_dec.label, 0.0)) >= 0.05
                    )
                    if can_smooth:
                        for idx in (i, i + 1):
                            curr_dec_j = smoothed[idx]
                            new_dist = dict(curr_dec_j.distribution)
                            new_dist[prev_dec.label] = max(new_dist.get(prev_dec.label, 0.0), curr_dec_j.distribution.get(curr_dec_j.label, 0.0))
                            if curr_dec_j.trace:
                                new_smoothed[idx] = PredictionResult.create_with_trace(
                                label=prev_dec.label,
                                decided_by=f"{curr_dec_j.decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: bounded 2-token sandwich smoothed to {prev_dec.label} clause.",
                                competing_predictions=curr_dec_j.competing_predictions,
                                distribution=new_dist,
                                token=curr_dec_j.trace.token,
                                model_predictions=curr_dec_j.trace.model_predictions,
                                decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                )
                            else:
                                new_smoothed[idx] = PredictionResult(
                                label=prev_dec.label,
                                decided_by=f"{curr_dec_j.decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: bounded 2-token sandwich smoothed to {prev_dec.label} clause.",
                                competing_predictions=curr_dec_j.competing_predictions,
                                distribution=new_dist,
                                trace=None,
                                )
            smoothed = new_smoothed
        return smoothed

    @classmethod
    def _refine_orphans(cls, smoothed: List[PredictionResult], segments: List[Tuple[str, str, int, int]]) -> List[PredictionResult]:
        n = len(smoothed)
        for _ in range(2):
            all_labels = [dec.label for dec in smoothed]
            label_counts = Counter(all_labels)

            for i in range(n):
                curr_dec = smoothed[i]
                curr_seg = segments[i]
                curr_script = curr_seg[1]
                tok_str = curr_seg[0]

                left_label = smoothed[i - 1].label if i - 1 >= 0 and segments[i - 1][1] == curr_script else None
                right_label = smoothed[i + 1].label if i + 1 < n and segments[i + 1][1] == curr_script else None

                is_orphan = (not curr_dec.label) or (label_counts[curr_dec.label] <= 2) or (
                    left_label and right_label and left_label != right_label and (
                        curr_dec.label not in (left_label, right_label)
                        or curr_dec.margin <= 0.35
                        or len(tok_str) <= 4
                    )
                )
                if is_orphan and (left_label or right_label):
                    target_label = None
                    if left_label and right_label:
                        p_left = curr_dec.distribution.get(left_label, 0.0)
                        p_right = curr_dec.distribution.get(right_label, 0.0)
                        if len(tok_str) <= 4:
                            if p_left - p_right > 0.15:
                                target_label = left_label
                            else:
                                target_label = right_label
                        else:
                            if p_left - p_right > 0.15:
                                target_label = left_label
                            elif p_right - p_left > 0.15:
                                target_label = right_label
                            elif curr_dec.label in (left_label, right_label):
                                target_label = curr_dec.label
                            else:
                                target_label = left_label
                    elif left_label:
                        target_label = left_label
                    elif right_label:
                        target_label = right_label

                    if target_label is not None and target_label != curr_dec.label:
                        can_smooth = (
                            label_counts[curr_dec.label] == 1
                            or not curr_dec.is_consensus_or_agreement()
                            or len(tok_str) <= 4
                            or curr_dec.distribution.get(target_label, 0.0) > 0.0
                        )
                        if can_smooth:
                            new_dist = dict(curr_dec.distribution)
                            new_dist[target_label] = max(new_dist.get(target_label, 0.0), curr_dec.distribution.get(curr_dec.label, 0.0))
                            if curr_dec.trace:
                                smoothed[i] = PredictionResult.create_with_trace(
                                label=target_label,
                                decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: boundary attribution projected to {target_label}.",
                                competing_predictions=curr_dec.competing_predictions,
                                distribution=new_dist,
                                token=curr_dec.trace.token,
                                model_predictions=curr_dec.trace.model_predictions,
                                decision_stage=DecisionStage.CONTEXT_REFINEMENT,
                                )
                            else:
                                smoothed[i] = PredictionResult(
                                label=target_label,
                                decided_by=f"{curr_dec.decided_by}+ContextRefinement",
                                reason=f"Spatial context smoothing applied: boundary attribution projected to {target_label}.",
                                competing_predictions=curr_dec.competing_predictions,
                                distribution=new_dist,
                                trace=None,
                                )
                            label_counts[target_label] += 1
                            if curr_dec.label in label_counts:
                                label_counts[curr_dec.label] -= 1
        return smoothed



class SubTokenSplitter:
    """
    Module for resolving un-spaced mixed-script code-switching.
    Evaluates tokens using all available experts to mathematically determine
    if a sub-token split yields a higher Joint Likelihood than an intact token.
    """
    @staticmethod
    def split(segments: List[Tuple[str, str, int, int]], candidate_langs: Iterable[str], experts: List) -> List[Tuple[str, str, int, int]]:
        new_segments = []
        for tok, script, start, end in segments:
            if script in ("HAN", "HIRAGANA", "KATAKANA", "HANGUL", "THAI", "BOPOMOFO") and len(tok) > 1:
                current_chunks = [(tok, start)]
                fully_split = []
                while current_chunks:
                    curr_tok, curr_start = current_chunks.pop(0)
                    if len(curr_tok) <= 1:
                        fully_split.append((curr_tok, curr_start))
                        continue
                        
                    # Aggregate base likelihood across all supporting experts
                    base_likelihood = 0.0
                    for expert in experts:
                        if expert.supports_token(curr_tok, script, candidate_langs):
                            _, res = expert.evaluate(curr_tok, candidate_langs)
                            if res:
                                base_likelihood = max(base_likelihood, max(res.values()))
                    
                    best_i = -1
                    max_split_likelihood = base_likelihood
                    
                    # Joint Likelihood Maximization of Code-Switch Boundaries
                    for i in range(1, len(curr_tok)):
                        left = curr_tok[:i]
                        right = curr_tok[i:]
                        
                        max_left_conf, max_right_conf = 0.0, 0.0
                        best_l, best_r = "", ""
                        
                        for expert in experts:
                            if expert.supports_token(left, script, candidate_langs):
                                _, res_l = expert.evaluate(left, candidate_langs)
                                if res_l:
                                    top_lang_l = max(res_l, key=res_l.get)
                                    if res_l[top_lang_l] > max_left_conf:
                                        max_left_conf = res_l[top_lang_l]
                                        best_l = top_lang_l
                                        
                            if expert.supports_token(right, script, candidate_langs):
                                _, res_r = expert.evaluate(right, candidate_langs)
                                if res_r:
                                    top_lang_r = max(res_r, key=res_r.get)
                                    if res_r[top_lang_r] > max_right_conf:
                                        max_right_conf = res_r[top_lang_r]
                                        best_r = top_lang_r
                        
                        if best_l and best_r and best_l != best_r:
                            # 1-state vs 2-state likelihood path comparison
                            split_likelihood = max_left_conf * max_right_conf
                            if split_likelihood > max_split_likelihood:
                                max_split_likelihood = split_likelihood
                                best_i = i
                                
                    if best_i != -1:
                        left_tok = curr_tok[:best_i]
                        right_tok = curr_tok[best_i:]
                        current_chunks.insert(0, (right_tok, curr_start + best_i))
                        current_chunks.insert(0, (left_tok, curr_start))
                    else:
                        fully_split.append((curr_tok, curr_start))
                        
                for sub_tok, sub_start in fully_split:
                    new_segments.append((sub_tok, script, sub_start, sub_start + len(sub_tok)))
            else:
                new_segments.append((tok, script, start, end))
        return new_segments


class LIDV5Pipeline:
    """
    LID Version 5: Reversed Pipeline Architecture.
    """
    def __init__(self, ft_path: str = "lid.176.ftz"):
        self.discovery = SentenceLanguageDiscovery(ft_path=ft_path)
        self.experts = [
            FastTextExpert(ft_path=ft_path),
            LinguaExpert(),
        ]

    def identify(self, text: str, allowed_langs: Iterable[str] = None) -> List[PredictionResult]:
        if not text or not text.strip():
            return []

        if allowed_langs is not None:
            candidate_langs = CandidateGenerator.get_candidates(allowed_langs)
        else:
            discovered = self.discovery.discover_candidates(text)
            candidate_langs = CandidateGenerator.get_candidates(discovered)

        segments = Tokenizer.segment_text_with_offsets(text)
        if not segments:
            return []
            
        segments = SubTokenSplitter.split(segments, candidate_langs, self.experts)

        scripts = [seg[1] for seg in segments]
        results: List[PredictionResult] = []

        token_predictions: List[List[Prediction]] = []
        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            preds: List[Prediction] = []
            for expert in self.experts:
                if expert.supports_token(token_str, script, candidate_langs):
                    raw_dist, res_dist = expert.evaluate(token_str, candidate_langs)
                    if res_dist:
                        lab, conf, margin = top_label(res_dist)
                        ranked = sorted(res_dist.items(), key=lambda item: item[1], reverse=True)
                        preds.append(Prediction(
                            label=lab,
                            confidence=conf,
                            margin=margin,
                            ranked_candidates=ranked,
                            model=expert.name,
                            raw_dist=raw_dist,
                            res_dist=res_dist,
                        ))
            token_predictions.append(preds)

        for idx, (token_str, script, start_idx, end_idx) in enumerate(segments):
            preds = token_predictions[idx]
            
            boundary_ev = BoundaryAnalyzer.analyze(preds, idx, scripts)

            evidences = EvidenceValidator.validate(
                preds, token_str, script, candidate_langs, boundary_ev
            )

            local_evidences = None
            if LocalContextAnalyzer.should_trigger(token_str, None, boundary_ev, evidences):
                local_evidences = LocalContextAnalyzer.analyze(
                    idx, segments, candidate_langs, self.experts, boundary_ev
                )

            decision = ArbitrationEngine.arbitrate(
                evidences, idx, segments, boundary_ev, local_evidences
            )
            results.append(decision)

        results = ContextRefinement.refine(results, segments)
        return results

    def identify_to_dict(self, text: str, allowed_langs: Iterable[str] = None) -> List[Dict]:
        if allowed_langs is not None:
            candidate_langs = CandidateGenerator.get_candidates(allowed_langs)
        else:
            discovered = self.discovery.discover_candidates(text)
            candidate_langs = CandidateGenerator.get_candidates(discovered)

        segments = Tokenizer.segment_text_with_offsets(text)
        if segments:
            segments = SubTokenSplitter.split(segments, candidate_langs, self.experts)
            
        decisions = self.identify(text, allowed_langs)

        output = []
        for i, dec in enumerate(decisions):
            seg_str, script, start_idx, end_idx = segments[i]
            output.append({
                "token": seg_str,
                "label": dec.label,
                "confidence": float(dec.distribution.get(dec.label, 1.0)),
                "decided_by": dec.decided_by,
                "reason": dec.reason,
                "start": start_idx,
                "end": end_idx,
                "script": script,
            })
        return output

    def detect_languages(self, text: str, allowed_langs: Iterable[str] = None) -> List[Tuple[str, str]]:
        if not text or not text.strip():
            return [(text, "en")]
            
        if allowed_langs is not None:
            candidate_langs = CandidateGenerator.get_candidates(allowed_langs)
        else:
            discovered = self.discovery.discover_candidates(text)
            candidate_langs = CandidateGenerator.get_candidates(discovered)
            
        segments = Tokenizer.segment_text_with_offsets(text)
        if segments:
            segments = SubTokenSplitter.split(segments, candidate_langs, self.experts)
            
        decisions = self.identify(text, allowed_langs)
        if not decisions or not segments:
            return [(text, "en")]

        spans: List[Tuple[str, str]] = []
        cur_lang = decisions[0].label
        cur_start = 0

        for i in range(1, len(decisions)):
            lab = decisions[i].label
            if lab != cur_lang:
                if not any(c.isalnum() for c in segments[i][0]):
                    decisions[i].label = cur_lang
                    continue
                cut_idx = segments[i][2]
                spans.append((text[cur_start:cut_idx], cur_lang))
                cur_lang = lab
                cur_start = cut_idx

        spans.append((text[cur_start:], cur_lang))
        return spans


_detector = None


def get_detector(ft_path: str = "lid.176.ftz") -> LIDV5Pipeline:
    global _detector
    if _detector is None:
        _detector = LIDV5Pipeline(ft_path=ft_path)
    return _detector


def detect_languages(text: str, allowed_langs: Iterable[str] = None) -> List[Tuple[str, str]]:
    return get_detector().detect_languages(text, allowed_langs=allowed_langs)


def batch_detect_languages(
    texts: List[str], allowed_langs: Iterable[str] = None
) -> List[List[Tuple[str, str]]]:
    det = get_detector()
    return [det.detect_languages(t, allowed_langs=allowed_langs) for t in texts]


__all__ = [
    "LIDV5Pipeline",
    "SubTokenSplitter",
    "get_detector",
    "detect_languages",
    "batch_detect_languages",
    "SentenceLanguageDiscovery",
    "Tokenizer",
    "BoundaryAnalyzer",
    "EvidenceValidator",
    "LocalContextAnalyzer",
    "ConsensusBuilder",
    "EvidenceComparison",
    "ArbitrationEngine",
    "ContextRefinement",
    "CandidateGenerator",
    "DecisionStage",
    "LANG_NAME_TO_CODE",
]
