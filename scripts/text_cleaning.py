"""
YaarAI Persian text cleaning utilities.

Design goals
- Conservative normalization suitable for semantic search / embeddings.
- Preserve meaningful Persian orthography (esp. ZWNJ usage) rather than deleting it wholesale.
- Remove harmful/control Unicode characters that corrupt text rendering and model input.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict

# Token-level fixes for common fused forms (mid-alef / contracted tokens).
# Note: this list is intentionally small and auditable.
MID_ALEF_REPLACEMENTS: Dict[str, str] = {
    "بیآموزد": "بی آموزد",
    "کآنجا": "که آنجا",
    "کآید": "که آید",
    "کآب": "که آب",
    "کآشفته": "که آشفته",
    "کآورد": "که آورد",
    "کآزمودم": "که آزمودم",
    "کآن": "که آن",
    "کآتش": "که آتش",
    "کآرزوی": "که آرزوی",
    "کآلوده": "که آلوده",
    "کآخر": "که آخر",
    "کآیینه": "که آیینه",
    "الآن": "الان",
}

CONTROL_CHARS = [
    "\u200e", "\u200f",        # LRM, RLM
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # embedding/override
    "\u2066", "\u2067", "\u2068", "\u2069",            # isolates
    "\u061c",                  # Arabic Letter Mark
]

DIACRITICS = [
    "\u064b", "\u064c", "\u064d", "\u064e",
    "\u064f", "\u0650", "\u0651", "\u0652",
    "\u0670",  # small alef
]


def apply_mid_alef_fixes(text: str) -> str:
    """Apply a small set of deterministic token-fusion fixes."""
    for bad, good in MID_ALEF_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return text


def clean_persian(text: str) -> str:
    """
    Conservative Persian text cleaning.

    Steps:
    1) NFC normalize
    2) Remove harmful control characters
    3) Normalize weird spaces
    4) Normalize Persian letters (yeh/kaf, etc.)
    5) Normalize heh+hamza forms into 'ه‌ی'
    6) Remove Arabic tashkil/diacritics
    7) Sanitize ZWNJ/ZWJ (keep valid intra-word usage)
    8) Collapse whitespace
    9) Apply mid-alef token fixes
    """
    if text is None:
        return ""

    # 1) Normalize Unicode
    text = unicodedata.normalize("NFC", text)

    # 2) Remove harmful control characters
    for ch in CONTROL_CHARS:
        text = text.replace(ch, "")

    # 3) Normalize weird spaces
    text = (
        text.replace("\u00A0", " ")   # NBSP
            .replace("\u202F", " ")  # narrow NBSP
            .replace("\u2007", " ")  # figure space
    )

    # 4) Normalize Persian letters
    text = text.replace("ي", "ی")  # Arabic Yeh → Persian Yeh
    text = text.replace("ى", "ی")  # Alef Maqsura → Persian Yeh
    text = text.replace("ك", "ک")  # Arabic Kaf → Persian Kaf

    # 5) Heh + hamza normalization (two forms)
    text = text.replace("ۀ", "ه‌ی")              # U+06C0
    text = re.sub(r"ه\u0654", "ه‌ی", text)      # Heh + combining hamza above

    # 6) Remove Arabic diacritics/tashkil
    for dia in DIACRITICS:
        text = text.replace(dia, "")

    # 7) Sanitize ZWNJ/ZWJ (safe version)
    # Keep ZWNJ between letters (valid: می‌رود، ره‌رو). Remove only illegal patterns.
    # Remove joiners between spaces
    text = re.sub(r"\s[\u200c\u200d]\s", " ", text)
    # Remove joiners before punctuation
    text = re.sub(r"[\u200c\u200d](?=[\s،.,:;?!])", "", text)
    # Remove joiners right after space
    text = re.sub(r"(?<=\s)[\u200c\u200d](?=\S)", "", text)
    # Collapse repeated joiners
    text = re.sub(r"[\u200c\u200d]{2,}", "\u200c", text)

    # 8) Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # 9) Mid-alef fixes
    text = apply_mid_alef_fixes(text)

    return text


__all__ = ["MID_ALEF_REPLACEMENTS", "apply_mid_alef_fixes", "clean_persian"]
