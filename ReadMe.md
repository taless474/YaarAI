# YaarAI

**YaarAI** is a retrieval-only Fal-e-Hafez system built around a simple constraint:

> Not all meaning should be computed.

The project uses semantic embeddings to retrieve **authentic Hafez bayts** by shared ethical and emotional stance, while deliberately avoiding poetry generation, paraphrase, or authoritative interpretation.

---

## Why this project exists

Hafez, a 14th-century Persian poet, writes about love as responsibility rather than possession; hope without entitlement; devotion without judgment. His poetry relies on implication, metaphor, and sometimes even form-level ambiguity. Explaining it in prose or generating “similar” verses often flattens what matters most.

Most modern LLM systems optimize for explanation, completion, and resolution.
Fal-e-Hafez requires the opposite: restraint.

YaarAI treats this tension not as a limitation, but as a design constraint.

---

## Core idea

Instead of asking:

> “What should the system say?”

YaarAI asks:

> “Which existing verse takes a similar position toward love, loss, or hope?”

To support this, the system:
- retrieves rather than generates;
- treats individual **bayts** as atomic meaning units;
- compares bayts to one another in a shared semantic space;
- uses semantic metadata (e.g. affect, ghazal axis) as constraints, not predictions;
- limits interpretation to optional, non-authoritative orientation.

The goal is not to explain Hafez, but to surface resonance.

---

## What YaarAI does

- Retrieves authentic Hafez bayts only; no poetry is generated.
- Uses precomputed bayt-level embeddings for similarity-based retrieval.
- Supports queries with or without an explicit question.
- Optionally adds minimal affective cues intended to shape how the verse lingers, similar to the aftertone of a song.
- Preserves ambiguity rather than resolving it.

---

## What YaarAI deliberately does *not* do

- Generate poetry or stylistic imitations
- Paraphrase or summarize verses
- Offer advice, prediction, or guidance
- Collapse ambiguity into explanation
- Optimize engagement or virality

These are non-goals by design, not missing features.

---

## Why retrieval is constrained

In Hafez, meaning is often:
- implicit rather than explicit,
- relational rather than referential,
- expressed through stance rather than statement,
- sometimes encoded in form itself.

Certain poetic techniques depend on ambiguity, repetition, or visual similarity between words whose meanings diverge only by syntactic boundary or spacing. Aggressive normalization or paraphrase destroys this layer of meaning entirely.

For this reason, YaarAI constrains computation to what can be done conservatively:
- retrieve instead of generate;
- surface resonance instead of explanation;
- respect form instead of normalizing it.

Embeddings are treated as a similarity heuristic, not as a model of semantic truth.

---
