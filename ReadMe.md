# YaarAI — Intent-Corresponding Semantic Retrieval for Hafez Ghazals

YaarAI is an **IntentCorresponding-Semantic-Retrieval** system for Hafez poems in form of Ghazal (similar to Fal-e-Hafez): you bring a *niyat* (intent), and the system returns a **real Hafez Ghazal beyt** whose *stance* resonates with that intent—without pretending to “explain” Hafez away.


- **HF dataset:** https://huggingface.co/datasets/taless474/hafez-ghazals-beyt-level-semantic-annotations
- **HF Space:** https://huggingface.co/spaces/taless474/yaarai-fal
- **Live demo (HTML Fal):** https://taless474-yaarai-fal.hf.space/fal/html


> **Note:** The public Space is a lightweight demo of the **Fal presentation + “semantic interface” rendering** (affect/lens phrasing rules). The larger project idea is the **intent → beyt retrieval** pipeline.

**Beyt**:(بیت) is a Persian poetry unit that’s basically a couplet. A beyt has two half-lines, and each half-line is called a mesra (مصراع).

---

## Core idea

Hafez, a 14th-century Persian poet, writes about love as responsibility rather than possession; hope without entitlement; devotion without judgment. His poetry relies on implication, metaphor, and sometimes even form-level ambiguity. Explaining it in prose or generating “similar” verses often flattens what matters most.

Most modern LLM systems optimize for explanation, completion, and resolution. Fal-e-Hafez requires the opposite: restraint.

YaarAI treats this tension not as a limitation, but as a design constraint.

YaarAI targets **position** instead of resemblance: the ethical/emotional stance a beyt takes toward love. In Hafez poems, meaning is often:

- implicit rather than explicit,
- relational rather than referential,
- expressed through stance rather than statement,
- sometimes encoded in form itself.

That creates a constraint that calls for:

- retrieve instead of generate;
- surface resonance instead of explanation;
- respect form instead of normalizing it.

Embeddings (and later, classifiers) are used as *search machinery*, not as a “reasoning engine.”

---

## The computational problem I actually cared about

When people speak about semantic search in poetry, they usually mean retrieving texts that resemble each other. That was not what I wanted.

I was not trying to retrieve verses that share vocabulary, imagery, or rhythm. I was trying to retrieve verses that take the same position toward love.

Positions such as:
- love as salvation rather than reward
- devotion without moral superiority
- longing without entitlement
- hope without accusation

Two beyts may share no visible words and still express the same stance. Conversely, two verses may look similar and mean something entirely different. The difference between resemblance and position is subtle; it is also decisive.

---
## What YaarAI does

At a high level, YaarAI is built around a *beyt-first contract*:

1. **Input:** a user’s question / niyat (in Persian; optionally English).
2. **Semantic interface layer (v1):** each beyt carries machine-usable semantic fields (affect, lens, short hint, etc.).
3. **Retrieval goal:** select a beyt whose stance corresponds to the intent (not merely lexical similarity).
4. **Output:**
   - the **beyt** (two **mesra**; often stored as a single string with a `/` separator in the dataset viewer)
   - **a minimal orientation line** (affect/lens phrasing) governed by strict “silence-aware” display rules

---

## Repo layout (high level)

- `scripts/` — product + pipeline code
  - `cli.py` — run Fal from the terminal
  - `retrieval.py` — weighted sampling retriever
  - `fal_assembly.py` — formatting / optional interpretation line
  - `embed_beyts.py` — build `data/embeddings/bayts_embeddings.npy`
  - `extract_ghazal_axis.py`, `extract_beyt_annotations.py` — API-based annotation (offline-precomputed in repo)
- `data/` — datasets, embeddings, annotations, reports
  - `data/raw/ghazals_with_insight.jsonl` — scraped verse + Ganjoor prose
  - `data/datasets/bayts_canonical_v1.jsonl` and `beyts_with_lens_v1.jsonl`— canonical beyt dataset used by the product
  - `data/embeddings/bayts_embeddings.npy` — embeddings used by retrieval
  - `data/annotations/` — `ghazal_axis`, `beyt_hint`, `affect`, `lens` artifacts + license note
  - `data/reports/` — diagnostics outputs (PCA/UMAP/cohesion/clustering)
- `assets/plots/` — shareable figures used in documentation
- `docs/` — design notes

- **Full Provenance**: what was built, in order in `build_log.md`

---

## Quickstart (run the Fal)

### Option A — run locally (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -e .

uvicorn app:app --reload --port 8000
```

Then open:

- HTML Fal page: `http://localhost:8000/fal/html`
- JSON API docs: `http://localhost:8000/docs`

### Option B — use the hosted demo

- Space: https://huggingface.co/spaces/taless474/yaarai-fal
- Live HTML Fal: https://taless474-yaarai-fal.hf.space/fal/html

---

## The semantic interface (what exists in v1)

The dataset and demo expose a small, deliberately conservative “semantic interface” that sits *between* retrieval and presentation.

### Dataset-level fields (v1)

From the public dataset viewer (`data/datasets/beyts_with_lens_v1.jsonl`), each record includes (at least):

- `poem_id` — which ghazal the beyt belongs to
- `beyt_id` — index of the beyt within the ghazal
- `text` — the beyt text (commonly two mesra separated by `/`)
- `affect` — a list of affect tags (0–2 items in the viewer)
- `beyt_hint` — a short, non-prose “orientation” hint
- `lens` — one of a small set of lens values
- `ghazal_axis` - a short, non-prose orientation of the ghazal beyt belongs to


### Presentation contract: “silence-aware” Fal assembly

The demo’s `assemble_fal()` is strict:

- The **beyt is always shown**.
- **Affect line**:
  - if “interpretation mode” is enabled, it becomes the (single) interpretation line.
- **Lens line**:
  - “hard” lens can be shown deterministically (if present),
  - “soft” lens is shown probabilistically (to avoid turning every Fal into a lecture).

This is not an accident: it is the project’s core constraint—**orientation without replacement**.

---

## Why YaarAI Exists

## *A story about Hafez, love, and constraints on computation*

I was fond of **Hafez** long before I could fully understand him.

As a child, I did not know all the words of his ghazals, and I certainly could not analyze them. Yet each poem felt like a story that quietly taught you how to be in love. Not how to possess love, not how to demand it, but how to remain open within it. There was sadness without bitterness; longing without accusation; hope without certainty.

Later, when I learned the language more deeply, I realized something precise and consistent. Hafez almost never criticizes the beloved. When he speaks of pain, he turns it inward. *If you do this, I will be sad; if you leave, I will be heartbroken.* The beloved is free. Love is not a contract, and it is never leverage.

This ethical posture toward love is central to Hafez’s poetry. His love is hopeful even when unfulfilled; gender-neutral in its address; and grounded in responsibility rather than entitlement.

---

## Hafez and contradiction

Hafez lived in a society where religious authority held real power. He often refers to himself as a Muslim, partly as protection. At the same time, his poetry is filled with wine, drunkenness, and the desire to escape rigid moral and material structures. This contradiction is not incidental; it is essential.

In one well-known verse, he writes:

> عشقت رسد به فریاد ار خود به سان حافظ
> قرآن ز بر بخوانی، بر چهارده روایت

A close meaning is: *Love will come to your rescue, even if, like Hafez, you know the Qur’an by heart in all fourteen accepted readings.*

This is not a rejection of religion; it is a declaration of priority. Love overrides every system that claims ultimate authority.

---

## Why Hafez matters beyond Persian literature

Hafez’s influence extends far beyond Persian-speaking cultures. Johann Wolfgang von Goethe, after encountering Hafez, regarded him not as an exotic poet but as an equal. Goethe wrote:

> “Hafiz, with thee alone,
> I wish to measure myself.”

This was not admiration at a distance; it was recognition. Goethe felt compelled to respond, not imitate. Hafez represented a worldview so internally coherent that it demanded engagement.

---

## Why prose explanations often destroy meaning

A common response to poetry is to “explain” it in prose. This is often where meaning collapses.

Consider the verse:

> زلف‌آشفته و خوی‌کرده و خندان‌لب و مست
> پیرهن‌چاک و غزل‌خوان و صراحی در دست

A typical prose rendering might describe disheveled hair, flushed cheeks, smiling lips, torn clothing, singing, and drinking. While not incorrect, such a paraphrase misses the point.

The verse is not cataloging appearance; it is asserting desirability. The beloved is most desirable precisely because she is unstyled, unconcerned with performance, fully herself, and playfully present in the world. This is an ethical and aesthetic claim, not a visual one.

Prose explanation flattens stance into description. In doing so, it removes the very commitment the verse is making about love.

For this reason, YaarAI avoids paraphrase generation entirely. Interpretation, when present, is limited to light orientation; it does not attempt to replace the poem’s meaning with explanatory text.

---

## A layer I didn’t want to lose: how a single word can “turn” without repeating itself

Sometimes Hafez makes beauty out of a word that returns, but not as repetition—more like a hinge.

For example:

> نه راه است این که بگذاری مرا بر خاک و بگریزی
> گذاری آر و بازم پرس تا خاک رهت گردم

Here **خاک** appears twice, but not as the same object.

- **بر خاک** is simply *on the ground*: abandonment, collapse, being left where one falls.
- **خاکِ رهت** is *the dust of your path*: chosen humility, devotion, self-effacement into the beloved’s movement.

They are not “related” in a tidy semantic way—one is physical ground, the other is a devotional metaphor—yet the echo binds the emotional motion of the couplet: from being thrown down to *volunteering* to become dust. The same syllable carries two different humiliations, and the second one transforms the first.

---

## When form itself carries meaning

In Hafez, meaning is not carried by words alone. Form itself can be semantic.

There are ghazals in which identical-looking phrases diverge in meaning solely because of spacing or syntactic boundary. For example, in the line:

> که با این درد اگر دربند درمانند، در مانند

A reader who rushes will see near-duplication; the poem is built on the fact that it is *not* duplication.

### 1) «دربندِ درمان‌اند» (dar-band-e darmān-and)

This is “در بندِ درمان‌اند”: *they are bound up in cure*—trapped in the pursuit of علاج, caught in the machinery of fixing, managing, resolving. It carries a quiet critique: even *seeking* remedy can become its own captivity.

### 2) «در مانند» (dar mānand)

This is from «ماندن»: *they remain*. Not “they get cured,” not “they get out,” but “they stay”—in the pain, in the state, in the condition.

So the line can flash two stances at once:

- *If, with this pain, they get trapped in the very idea of cure…*
- *…they will simply remain.*

The closeness of the surface (درمانند / در مانند) is the point: one extra boundary changes the ethics of the sentence. The ambiguity is deliberate. The poem depends on the reader noticing it.

This is not noise; it is technique.

Any system that treats poetry as interchangeable text units, or that aggressively normalizes form, will erase this dimension of meaning entirely.

---

## Constraint on computation

These observations impose a constraint on computation.

The constraint is not technical; it is semantic. Certain aspects of meaning in Hafez are implicit rather than explicit; relational rather than referential; encoded in stance, not statement; sometimes embedded in form itself.

Such meaning cannot be reliably extracted, summarized, or paraphrased without loss. Therefore, the system must be designed not to maximize interpretation, but to limit it.

In YaarAI, computation is constrained to what it can do conservatively. Embeddings are used as a search mechanism, not as a reasoning engine. They help locate proximity in meaning; they do not claim to capture meaning exhaustively.

---

## Why existing systems did not work for me

I encountered systems that used strong multilingual embedding models to retrieve poetry across multiple poets. Technically, these systems were sound. Conceptually, they failed my use case.

Mixing poets flattened worldview. Treating Hafez as interchangeable erased precisely what distinguishes him. Retrieval favored surface resemblance while missing ethical posture and metaphorical commitment.

The limitation was not the model; it was the definition of similarity.

---

## What this system refuses to do

YaarAI does not attempt to:

- generate poetry
- explain poems authoritatively
- offer advice or prediction
- collapse ambiguity
- optimize engagement

Fal-e-Hafez has endured because it leaves space for the reader. This system is designed to preserve that space.

---

## Closing

YaarAI is not an attempt to modernize Hafez, interpret him, or improve upon him. It is an attempt to build a computational system that knows where computation must stop.

Love, in Hafez’s sense, does not need resolution; it needs room.

---

## Licensing

- **Dataset:** CC BY-NC 4.0 (see the dataset page for the current license declaration)
- **Code:** MIT (see `LICENSE`)




---
