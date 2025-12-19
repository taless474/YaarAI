# YaarAI — Semantic Space Findings (Bayt-Level)

This document records the conclusions from exploratory semantic analysis of **bayt-level embeddings** in YaarAI.

The goal of this phase was **not** to optimize embeddings, but to understand whether Hafez’s bayts form an interpretable semantic space suitable for retrieval.

---

## 1. Scope of Analysis

- Unit of analysis: **individual bayts** (not ghazals)
- Dataset size: ~4,200 authentic Hafez bayts
- Language: Persian only
- Input representation (exploratory):
  - `bayt_hint`
  - `affect` (0–2 labels)
  - optional `ghazal_axis` (contextual)
- Model used for probing: `BAAI/bge-m3`
- Methods:
  - cosine embeddings
  - PCA (diagnostic)
  - UMAP (visual inspection)
  - KMeans + HDBSCAN (interpretability checks)

This phase is **diagnostic only**. Results below inform production design decisions.

---

## 2. Primary Observation: Affect Dominates Bayt-Level Semantics

Across all visualizations and cluster inspections, the dominant organizing principle of the bayt semantic space is **affective stance**, not topic.

Observed coherent regions include:
- امید (hope / grace)
- اندوه / حسرت (grief, loss, nostalgia)
- شوق (longing, attraction)
- حیرت (wonder, epistemic uncertainty)
- بی‌قراری (restlessness, agitation)
- آرامش (acceptance, detachment)

These regions are:
- contiguous but **not sharply bounded**
- overlapping in meaningful ways
- stable across clustering methods

This behavior aligns with the poetic ontology of Hafez and supports affect as a first-class semantic signal.

---

## 3. bayt_hint Quality and Behavior

- `bayt_hint` phrases do **not** collapse into a few generic abstractions
- Each cluster contains high lexical variety with semantic coherence
- No evidence of directive leakage or over-normalization

Conclusion:
> `bayt_hint` successfully captures *local event semantics* without overpowering tone.

---

## 4. ghazal_axis Acts as Context, Not Driver

Empirical findings:
- The same `ghazal_axis` appears across multiple bayt clusters
- No cluster is defined by a single axis
- Axis labels cut *across* affective regions

Conclusion:
> `ghazal_axis` should be treated as **contextual metadata**, not as a primary signal in bayt embeddings.

Strong injection of `ghazal_axis` into bayt embeddings would blur meaningful local distinctions.

---

## 5. Cluster Structure Is Porous but Interpretable

Clusters derived from KMeans and HDBSCAN show:
- strong internal semantic consistency
- soft boundaries between related affective modes
- expected overlap between longing / grief / hope regions

This is considered **desirable**, not a flaw.

Hafez’s bayts naturally inhabit overlapping emotional and conceptual states.

---

## 6. Visualization Principles Established

UMAP was used **only** as a diagnostic tool.

Effective visualizations included:
- UMAP colored by dominant affect (most informative)
- UMAP colored by cluster ID (secondary)
- Faceted UMAPs per affect (confirmatory)

Explicitly avoided:
- interpreting UMAP distances quantitatively
- optimizing embeddings to improve visual separation

---

## 7. Frozen Conclusions for Production Design

From this exploration, the following constraints are fixed:

1. Bayts are the correct semantic retrieval unit
2. Affect must be preserved in embedding design
3. `bayt_hint` is the core abstraction layer
4. `ghazal_axis` remains contextual, not local
5. A single bayt-level semantic space is sufficient

Any future change to embedding strategy should be justified against these findings.

---

## 8. Design Implication Summary (One Sentence)

> Bayt-level semantics in Hafez organize primarily along affective and stance dimensions, with local event abstraction providing structure and global ghazal themes acting only as context.

---

*This document intentionally avoids model-specific or implementation-specific details. It records semantic facts observed in the data.*
