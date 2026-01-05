# Design Decisions

This document records the major architectural and semantic decisions behind YaarAI.
Each decision is intentional and grounded in the constraints described in `docs/story.md`.

The guiding principle throughout the system is restraint: computation is used where it preserves meaning, and constrained where it would collapse ambiguity.

---

## Proposed semantic retrieval method

YaarAI implements a constrained semantic retrieval method designed specifically for Fal-e-Hafez.

The system is structured around three explicitly separated semantic layers:

1. **Textual unit (bayt)**
   The atomic unit of retrieval is the individual bayt. Each bayt is treated as a self-contained semantic moment rather than as part of a linear narrative.

2. **Semantic proximity (embeddings)**
   Bayts are embedded into a shared vector space. These embeddings are used to estimate proximity between bayts themselves, serving as a similarity heuristic rather than an interpretation of user intent or meaning.

   At the current stage, retrieval is driven primarily by bayt-to-bayt similarity. User queries, when present, act as a coarse selector or lens rather than as a fully modeled semantic target.

3. **Semantic orientation (metadata)**
   Each bayt is annotated offline with conservative semantic metadata, including:
   - affect (emotional register)
   - ghazal_axis (thematic or ethical orientation of the ghazal)

   These annotations function as semantic constraints or priors during retrieval, not as prediction targets.

At query time, the system:
- embeds bayts into a shared semantic space;
- selects candidate bayts based on proximity;
- optionally filters or re-ranks candidates using affect and ghazal_axis metadata;
- returns a single authentic bayt, optionally accompanied by a minimal affective cue.

No generative step is involved in meaning formation. All semantics are retrieved or selected from curated structures.

---

## Retrieval-only; no poetry generation

**Decision**
YaarAI retrieves authentic Hafez bayts only; it never generates poetry or stylistic imitations.

**Rationale**
Hafez’s poetry relies on implication, metaphor, and ambiguity. Generative models tend to resolve uncertainty by producing explicit continuations, which flattens ethical and emotional stance. Retrieval preserves the original text and keeps interpretation with the reader.

**Tradeoff**
- Limits expressive flexibility.
- Prevents creative reformulation.

---

## Single-poet corpus

**Decision**
The corpus is restricted to Hafez only.

**Rationale**
Hafez’s worldview toward love, devotion, and responsibility is internally consistent and distinct. Mixing poets collapses worldview into surface similarity and erases ethical posture.

**Tradeoff**
- Smaller corpus.
- Reduced stylistic diversity.

---

## Bayt-level retrieval with ghazal-level orientation

**Decision**
Bayts are the retrieval unit. Ghazal-level semantics are represented through explicit `ghazal_axis` annotations rather than ghazal text embeddings.

**Rationale**
Ghazals establish an ethical or emotional field rather than a linear narrative. Embedding full ghazals over-smooths meaning and reduces precision. Using ghazal axes as metadata preserves worldview without sacrificing bayt-level specificity.

**Tradeoff**
- Requires careful manual definition of axes.
- Does not capture themes outside the predefined set.

---

## Offline semantic annotation

**Decision**
Affect and ghazal_axis annotations are created offline and stored in the dataset.

**Rationale**
Offline annotation allows conservative, reviewable semantics and avoids runtime drift. It keeps system behavior stable and inspectable.

**Tradeoff**
- Manual curation effort.
- Slower semantic iteration.

---

## Optional affective cues

**Decision**
The system may optionally attach a short affective cue to the returned bayt.

**Rationale**
The cue is intended to shape how the verse lingers, similar to the aftertone of a song, without explaining or summarizing the poem.

**Constraints**
- The cue must be removable without loss of meaning.
- It must not restate the bayt.
- It must not introduce advice or interpretation.

---

## No prose paraphrase or explanation

**Decision**
The system never paraphrases or explains bayts in prose.

**Rationale**
Prose explanation collapses ethical stance into surface description. In Hafez, meaning is often asserted implicitly and cannot be preserved through paraphrase.

---

## Preservation of form

**Decision**
Text normalization is conservative; form-level distinctions are preserved where possible.

**Rationale**
Some bayts encode meaning through repetition, spacing, or syntactic boundary. Aggressive normalization erases form-dependent semantics.

---

## Probabilistic restraint

**Decision**
Non-essential additions, such as affective cues, are applied probabilistically.

**Rationale**
Predictability undermines the experience of encounter. Controlled randomness preserves freshness without introducing chaos.

---

## Explicit non-goals

YaarAI explicitly does not attempt to:
- advise, predict, or guide users;
- resolve ambiguity;
- optimize engagement;
- learn from user input online.

These are design boundaries, not missing features.

---

## Summary

The central design question of YaarAI is not model selection but boundary selection: deciding where computation preserves meaning and where it would destroy it. All decisions in this document follow from that constraint.
