# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
# ---

# %% [markdown]
# ### Validation of Bayt-Level Semantic Annotations (YaarAI)
#
# This notebook validates **bayt-level semantic annotations** used in YaarAI,
# including:
#
# - `bayt_hint`: a short noun phrase describing what happens in the bayt
# - `affect`: up to two affect labels drawn from a fixed vocabulary
#
# The goals of this notebook are to:
# - verify schema correctness,
# - inspect annotation distributions,
# - validate repairs and normalizations,
# - perform random qualitative checks with full bayt context.
#
# This notebook performs no regeneration.

# %%
import json
import random
import re
from pathlib import Path
from collections import Counter, defaultdict

# %% [markdown]
# ### Load raw bayt text
#
# Raw bayt text is loaded once and reused throughout the notebook
# to provide full poetic context during inspection.

# %%
RAW_PATH = Path("../data/raw/ghazals_with_insight.jsonl")

raw_by_key = {}
raw_by_poem = defaultdict(list)

with RAW_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        key = (r["poem_id"], r["bayt_id"])
        raw_by_key[key] = r["text"]
        raw_by_poem[r["poem_id"]].append(r)

len(raw_by_key)

# %% [markdown]
# ### Why multiple bayt annotation versions exist
#
# Bayt-level semantic annotations in YaarAI were refined through a
# **multi-stage, quality-driven process**.
#
# Rather than overwriting results, each refinement produced a new version
# to ensure transparency, reproducibility, and auditability.
#
# The annotation versions are:
#
# - **v1 — Initial extraction**
#   First-pass GPT-4.1 extraction of:
#   - `bayt_hint`: a short noun phrase describing what happens in the bayt
#   - `affect`: up to two affect labels from a fixed vocabulary
#
# - **v1.1 — Conciseness & drift repair**
#   An automated repair pass applied to bayt hints that exceeded a length
#   threshold or showed interpretive / explanatory drift.
#   This step improved abstraction while preserving meaning.
#
# - **v1.2 — Directive normalization (explicit)**
#   Deterministic, rule-based removal of explicit directive framing such as:
#   - «دعوت به …»
#   - «توصیه به …»
#   - «تشویق به …»
#
# - **v1.3 — Directive normalization (residual)**
#   Final normalization pass removing residual *soft directive* prefixes
#   left behind after earlier repairs, including:
#   - «توجه به …»
#   - «بهره‌گیری از …»
#
#   This step completes the transition to **fully descriptive,
#   non-directive bayt hints**, without regeneration or semantic reinterpretation.
#
# This notebook validates the **final canonical version (v1.3)**.
# Earlier versions are retained for reference and provenance.

# %%
ANNOTATION_PATH = Path("../data/annotations/bayt_annotations_v1_3.jsonl")

rows = []
with ANNOTATION_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

len(rows)

# %% [markdown]
# ### What is validated in this notebook
#
# This notebook validates the **final canonical bayt annotation layer (v1.3)**.
#
# The following aspects are checked:
#
# - schema correctness (`poem_id`, `bayt_id`, `bayt_hint`, `affect`)
# - conciseness of `bayt_hint` (noun phrase, not prose)
# - absence of directive or verbal framing
# - reasonable distribution of affect labels
# - semantic alignment between bayt text, hint, and affect
#
# All checks are **diagnostic and qualitative**.
# No further annotation, regeneration, or normalization is performed here.

# %%
for r in rows:
    assert isinstance(r["poem_id"], int)
    assert isinstance(r["bayt_id"], int)
    assert isinstance(r["bayt_hint"], str)
    assert r["bayt_hint"].strip()
    assert isinstance(r["affect"], list)
    assert len(r["affect"]) <= 2

# %% [markdown]
# ### Bayt hint length statistics
#
# Bayt hints should remain short noun phrases, not explanatory prose.

# %%
lengths = [len(r["bayt_hint"].split()) for r in rows]

min(lengths), max(lengths), round(sum(lengths) / len(lengths), 2)

# %% [markdown]
# ### Inspection of long bayt hints
#
# Bayt hints exceeding a length threshold are inspected manually
# to detect interpretive drift.

# %%
long_hints = [r for r in rows if len(r["bayt_hint"].split()) >= 8]
len(long_hints)

# %%
for r in long_hints:
    key = (r["poem_id"], r["bayt_id"])
    print(f"poem_id={r['poem_id']} bayt_id={r['bayt_id']}")
    print("BAYT:", raw_by_key.get(key))
    print("HINT:", r["bayt_hint"])
    print("-" * 80)

# %% [markdown]
# ### Affect label distribution
#
# We inspect the frequency of affect labels to ensure reasonable coverage
# and detect skew or collapse.

# %%
affects = [a for r in rows for a in r["affect"]]
Counter(affects)

# %% [markdown]
# ### Affect cardinality check
#
# Each bayt may have 0, 1, or 2 affect labels.

# %%
Counter(len(r["affect"]) for r in rows)

# %% [markdown]
# ### Random global inspection
#
# A random sample of bayts is inspected to verify overall annotation quality.

# %%
random.seed(42)

for r in random.sample(rows, 10):
    key = (r["poem_id"], r["bayt_id"])
    print(f"poem_id={r['poem_id']} bayt_id={r['bayt_id']}")
    print("BAYT:", raw_by_key[key])
    print("HINT:", r["bayt_hint"])
    print("AFFECT:", r["affect"])
    print("-" * 80)

# %% [markdown]
# ### Inspection of normalized bayt hints
#
# Bayt hints modified by rule-based normalization are inspected
# to ensure semantic content was preserved.

# %%
normalized = [
    r for r in rows
    if r.get("annotation_meta", {}).get("manual_norm") is True
]

len(normalized)

# %%
random.seed(42)

for r in random.sample(normalized, 10):
    key = (r["poem_id"], r["bayt_id"])
    print(f"poem_id={r['poem_id']} bayt_id={r['bayt_id']}")
    print("BAYT:", raw_by_key[key])
    print("HINT:", r["bayt_hint"])
    print("-" * 80)

# %% [markdown]
# ### Affect-specific slice inspection
#
# We inspect bayts sharing the same affect label to verify semantic coherence.

# %%
subset = [r for r in rows if "حسرت" in r["affect"]]

random.seed(123)

for r in random.sample(subset, 8):
    key = (r["poem_id"], r["bayt_id"])
    print(f"poem_id={r['poem_id']} bayt_id={r['bayt_id']}")
    print("BAYT:", raw_by_key[key])
    print("HINT:", r["bayt_hint"])
    print("AFFECT:", r["affect"])
    print("-" * 80)
