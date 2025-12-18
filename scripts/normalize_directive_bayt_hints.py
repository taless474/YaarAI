# %%
"""
Normalize directive framing in bayt_hints.

This script removes directive prefixes such as:
- دعوت به
- توصیه به
- تشویق به
- توجه به
- بهره‌گیری از

from bayt_hint fields, preserving the remaining noun phrase.

No regeneration, no semantic reinterpretation.
A new annotation version (v1.3) is written.

Input:
  data/annotations/bayt_annotations_v1_2.jsonl

Output:
  data/annotations/bayt_annotations_v1_3.jsonl
"""

# %%
import json
from pathlib import Path
import copy

# %%
IN_PATH = Path("data/annotations/bayt_annotations_v1_2.jsonl")
OUT_PATH = Path("data/annotations/bayt_annotations_v1_3.jsonl")

# %%
DIRECTIVE_PREFIXES = (
    "دعوت به",
    "توصیه به",
    "تشویق به",
    "توجه به",
    "بهره‌گیری از",
)


# %%

# %%
def normalize_hint(hint: str) -> str | None:
    """
    If hint starts with a directive prefix, remove it.
    Return normalized hint, or None if no change.
    """
    for p in DIRECTIVE_PREFIXES:
        if hint.startswith(p):
            new_hint = hint[len(p):].strip()
            return new_hint if new_hint else None
    return None


# %%
def main():
    assert IN_PATH.exists(), f"Input file not found: {IN_PATH}"
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    changed = 0

    with IN_PATH.open("r", encoding="utf-8") as fin, \
         OUT_PATH.open("w", encoding="utf-8") as fout:

        for line in fin:
            r = json.loads(line)
            total += 1

            r_new = copy.deepcopy(r)
            old_hint = r_new["bayt_hint"]
            new_hint = normalize_hint(old_hint)

            if new_hint is not None:
                r_new["bayt_hint"] = new_hint

                meta = r_new.get("annotation_meta", {})
                meta.update({
                    "manual_norm": True,
                    "manual_norm_rule": "remove_directive_prefix",
                })
                r_new["annotation_meta"] = meta

                changed += 1

            fout.write(json.dumps(r_new, ensure_ascii=False) + "\n")

    print(f"Processed {total} rows")
    print(f"Normalized {changed} bayt_hints")


# %%
if __name__ == "__main__":
    main()
