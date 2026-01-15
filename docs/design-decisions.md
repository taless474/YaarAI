# Design decisions

This document records the key architectural decisions behind **YaarAI** (v1).
Goal: a Fal-e-Hafez experience that is authentic, reproducible, and semantically grounded without “inventing” Hafez.

## Retrieval-only: never generate Hafez
- YaarAI returns **only authentic Hafez beyts** from the curated corpus.
- The system does **not** generate new poetry or stylistic imitations.

**Why:** preserves authenticity, ambiguity, and trust.

## Beyt is the atomic unit
- The retrieval unit is the **beyt** (two **mesra**).
- Ghazals can shift stance/emotion across beyts, so beyt-level retrieval stays precise.

## Embeddings are used for proximity, not reasoning
- Embeddings are a **similarity heuristic** to propose candidate beyts.
- They do not “understand” intent; they provide neighborhood structure.

## Semantic orientation is metadata, computed offline
- YaarAI uses conservative, reviewable annotations as metadata:
  - `ghazal_axis` (ghazal-level orientation)
  - `beyt_hint` (a phrase on beyt meaning)
  - `affect` (closed vocabulary of 8)
  - `lens` (secondary framing axis; 7 lenses)

**Why:** stable behavior, reproducible outputs, fewer runtime surprises.

## Closed vocabulary for affect
- Affect labels are restricted to an approved set.
- This prevents label drift and keeps evaluation meaningful.

## Ghazal-level signals are not embedded into retrieval probes
- Diagnostics showed that injecting ghazal identity into probes can inflate cohesion metrics.
- Cohesion tests are run on representations that avoid leaking ghazal membership.

## Lenses: a second axis beyond affect
- Lenses capture interpretive framing (e.g., stance/relational structure) that affect alone misses.
- Current lenses are validated; supervised calibration is planned after expanding labels.

## Product-first: keep v1 scripts working
- Core scripts such as `fal_assembly.py` and `retrieval.py` remain the stable execution path.
- Refactors happen only when they do not break the working product.

## Licensing boundary
- Repository **code** is MIT-licensed.
- Derived data artifacts follow the upstream dataset license (**CC BY-NC 4.0**) with attribution.

## Evaluation and diagnostics summary
We track a small set of checks to ensure the embedding space and axes are usable:

- **Neighborhood sanity checks:** nearest-neighbor samples should be semantically plausible to a Persian reader.
- **Ghazal cohesion:** measure how often kNN neighbors share the same `poem_id` vs a random baseline (used as a diagnostic, not a goal).
  - k=20: mean **0.1413**, median **0.10** vs random baseline **0.00217** (~65× above random).
  - Probe variants showed near-zero cohesion without ghazal leakage; including `ghazal_axis` inflates cohesion, so we exclude it in cohesion diagnostics.
- **Affect kNN coherence:** quantify whether neighbors share affect labels above chance; use failures to refine vocabulary/labels.
- **Affect centroid diagnostics:** compute per-affect centroids and inspect overlap/collapse to detect indistinguishable affects.
- **UMAP sweeps:** parameter sweeps to ensure visual structure is not cherry-picked (UMAP is a visualization aid, not proof).
- **Lens confidence via margin:** track `best` vs `second` lens score margin to estimate coverage/ambiguity and prioritize manual labeling.
