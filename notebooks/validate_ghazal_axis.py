# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python (yaarai)
#     language: python
#     name: yaarai
# ---

# %% [markdown]
# ### Validation of Ghazal-Level Semantic Axes (YaarAI)
#
# This notebook validates the **ghazal_axis** annotations generated for the YaarAI project.
#
# The goal is to ensure that:
# - each ghazal has a valid abstract semantic axis,
# - axes are concise noun phrases (not prose),
# - no verbal or directive language leaks into the annotations,
# - axes apply coherently across all bayts of a ghazal.
#
# This notebook is intended for **inspection and validation only**.
# No annotation or regeneration is performed here.
#

# %%
import json
import random
import re
from pathlib import Path
from collections import Counter, defaultdict

# %% [markdown]
# ### Load ghazal axis annotations
#
# We load the ghazal-level semantic axis annotations from disk and verify
# that the expected number of entries is present.

# %%
PATH = Path("../data/annotations/ghazal_axis_v1.jsonl")

rows = []
with PATH.open("r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

len(rows) # there are 495 ghazals in Divan-e-Hafez

# %% [markdown]
# ### Schema sanity check
#
# Each record must:
# - contain an integer `poem_id`
# - contain a non-empty string `ghazal_axis`
#

# %%
for r in rows:
    assert isinstance(r["poem_id"], int)
    assert isinstance(r["ghazal_axis"], str)
    assert r["ghazal_axis"].strip()


# %% [markdown]
# ### Axis length statistics
#
# We inspect the length (in words) of ghazal axes to ensure they remain
# short abstract noun phrases rather than explanatory prose.
#

# %%
lengths = [len(r["ghazal_axis"].split()) for r in rows]

min(lengths), max(lengths), round(sum(lengths) / len(lengths), 2)

# %% [markdown]
# ### Inspection of long axes
#
# Axes with unusually large word counts are inspected manually to ensure
# they are still semantically justified and not overly verbose.
#

# %%
long_axes = [r for r in rows if len(r["ghazal_axis"].split()) >= 8]
len(long_axes)

# %%
for r in long_axes:
    print(len(r["ghazal_axis"].split()), "→", r["ghazal_axis"])

# %% [markdown]
# ### Verb-surface diagnostic (heuristic)
#
# As a diagnostic step, we scan for verb-like surface forms.
# This is not an error detector, but a sanity check against accidental
# prose leakage.

# %%
verb_like = re.compile(r"(می‌|می |کرد|شد|است|بود)")

bad = [r for r in rows if verb_like.search(r["ghazal_axis"])]
print(len(bad))
bad

# %% [markdown]
# ### Axis frequency distribution
#
# We inspect the most frequent axes to understand the high-level
# semantic structure of the dataset and detect possible degeneracy.

# %%
axes = [r["ghazal_axis"] for r in rows]
Counter(axes).most_common(20)

# %% [markdown]
# ### Deep inspection of a frequent axis
#
# We select a frequent axis and inspect all bayts of its ghazals to ensure
# the axis applies coherently across the poem.
#

# %%
target_axis = "جستجوی حقیقت پنهان"

matching = [
    r for r in rows
    if r["ghazal_axis"] == target_axis
]

len(matching)

# %% [markdown]
# ### Load raw ghazal text
#
# To contextualize axes, we load the original bayts for each ghazal.

# %%
RAW_PATH = Path("../data/raw/ghazals_with_insight.jsonl")

raw_by_poem = defaultdict(list)
with RAW_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        raw_by_poem[r["poem_id"]].append(r)

# %% [markdown]
# ### Inspect bayts under selected axis
#
# Each ghazal assigned to the selected axis is printed in full to confirm
# semantic alignment.
#

# %%
for r in matching:
    pid = r["poem_id"]
    print("=" * 60)
    print(f"poem_id = {pid}")
    print("AXIS:", r["ghazal_axis"])
    print("BAYTS:")
    for b in raw_by_poem[pid]:
        print("-", b["text"])


# %% [markdown]
# ### Inventory of all semantic axes
#
# This provides a full human-readable overview of the abstract semantic
# space covered by the dataset.

# %%
for axis in sorted(set(axes)):
    print(axis)

# %% [markdown]
# ### Random global sanity check
#
# A small random sample of ghazals is inspected to ensure no anomalies
# remain after all validation steps.

# %%
random.seed(42)

for r in random.sample(rows, 3):
    print("AXIS:", r["ghazal_axis"])
    print("BAYTS:")
    for b in raw_by_poem[r["poem_id"]]:
        print("-", b["text"])
    print("-" * 40)
