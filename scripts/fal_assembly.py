# scripts/fal_assembly.py
from __future__ import annotations

from typing import Any, Mapping, Sequence
import random

from .language.affect_variants import AFFECT_VARIANTS
from .language.lens_soft import LENS_VARIANTS_SOFT
from .language.lens_hard import LENS_VARIANTS_HARD


# ---------------------------------------------------------------------
# Presentation flag (controlled by CLI)
# ---------------------------------------------------------------------
INTERPRET: bool = True


def set_interpret(value: bool) -> None:
    """Enable / disable interpretation mode (presentation only)."""
    global INTERPRET
    INTERPRET = bool(value)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _pick_variant(variants: Mapping[str, Sequence[str]], key: str) -> str | None:
    vals = variants.get(key)
    if not vals:
        return None
    return random.choice(list(vals)).strip()


def _should_show_soft_lens(prob: float = 0.30) -> bool:
    return random.random() < prob


# ---------------------------------------------------------------------
# Public API (DO NOT CHANGE SIGNATURE)
# ---------------------------------------------------------------------
def assemble_fal(beyt: Mapping[str, Any]) -> str:
    """
    Beyt-first, silence-aware Fal assembly.

    Rules:
    - Beyt text is always shown
    - Affect:
        - if INTERPRET is False → may show affect line
        - if INTERPRET is True  → affect becomes the interpretation line
    - Lens:
        - hard lens → shown deterministically (if present)
        - soft lens → shown with ~30% probability (if present)
    - No hardcoded language strings
    """

    lines: list[str] = []

    # -----------------------------------------------------------------
    # 1) Beyt (always)
    # -----------------------------------------------------------------
    text = str(beyt.get("text", "")).strip()
    if text:
        lines.append(text)

    # -----------------------------------------------------------------
    # 2) Affect handling
    # -----------------------------------------------------------------
    affects = beyt.get("affect") or []
    if INTERPRET and isinstance(affects, list) and affects:
        affect_key = str(affects[0]).strip()
        affect_line = _pick_variant(AFFECT_VARIANTS, affect_key)
        if affect_line:
            lines.append(affect_line)

    # -----------------------------------------------------------------
    # 3) Lens handling
    # -----------------------------------------------------------------
    lens = beyt.get("lens")
    if lens:
        lens_key = str(lens).strip()

        # Hard lens: deterministic
        if lens_key in LENS_VARIANTS_HARD:
            lens_line = _pick_variant(LENS_VARIANTS_HARD, lens_key)
            if lens_line:
                lines.append(lens_line)

        # Soft lens: probabilistic (~30%)
        elif lens_key in LENS_VARIANTS_SOFT:
            if _should_show_soft_lens(0.30):
                lens_line = _pick_variant(LENS_VARIANTS_SOFT, lens_key)
                if lens_line:
                    lines.append(lens_line)

    # -----------------------------------------------------------------
    # Final output
    # -----------------------------------------------------------------
    return "\n".join([ln for ln in lines if ln.strip()]).strip()
