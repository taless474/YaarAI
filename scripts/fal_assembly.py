# scripts/fal_assembly.py

import random
from typing import Optional

from .types import BaytRow
from .config import SOFT_LENSES, HARD_LENSES, DEFAULT_MARKER


def choose_variant(options):
    return random.choice(options)


def render_affect_block(affect, affect_variants):
    """
    Returns a single line combining affect sentences,
    or None if affect is empty.
    """
    lines = []
    for a in affect:
        opts = affect_variants.get(a)
        if opts:
            lines.append(choose_variant(opts))
    return " ".join(lines) if lines else None


def render_lens_block(
    lens: Optional[str],
    lens_soft,
    lens_hard,
):
    """
    Returns one lens sentence, or None.
    """
    if lens in HARD_LENSES:
        return choose_variant(lens_hard[lens])
    if lens in SOFT_LENSES:
        return choose_variant(lens_soft[lens])
    return None


def assemble_fal(
    row: BaytRow,
    *,
    affect_variants,
    lens_soft,
    lens_hard,
) -> str:
    """
    Assembly contract (bayt-first):

    Case A: affect ≠ ∅, lens = None
      → Bayt + Affect

    Case B: affect ≠ ∅, lens ≠ None
      → Bayt + Affect + Lens

    Case C: affect = ∅, lens = None
      → Bayt + DEFAULT_MARKER  (بیت گویاست)

    Case D: affect = ∅, lens ≠ None
      → Bayt + Lens
    """
    bayt = row["text"].strip()
    affect = row.get("affect") or []
    lens = row.get("lens")

    blocks = [bayt]

    affect_line = render_affect_block(affect, affect_variants)
    if affect_line:
        blocks.append(affect_line)

    lens_line = render_lens_block(lens, lens_soft, lens_hard)
    if lens_line:
        blocks.append(lens_line)

    if not affect and lens is None:
        blocks.append(DEFAULT_MARKER)

    return "\n".join(blocks)
