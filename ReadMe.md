# YaarAI 🌙

YaarAI is a semantic Fal-e-Hafez system focused on love- and relationship-oriented questions.

Instead of generating poetry, YaarAI always returns **an authentic couplet (bayt) by Hafez**, selected through semantic retrieval, along with a **short modern Persian interpretation** written in a casual, contemporary tone.

The project is designed to preserve literary authenticity while enabling modern, relatable interaction.

---

## Core Principles

- **No poetry generation**  
  All verses come from a verified Hafez corpus. Nothing is fabricated or paraphrased.

- **Semantic retrieval, not keyword matching**  
  Bayts are selected based on meaning and emotional alignment.

- **Clear thematic scope**  
  The system only responds within a constrained set of relationship-related themes.

- **Separation of concerns**  
  Classical text is kept intact; modern interpretation is clearly marked and stylistically distinct.

---

## Supported Themes

YaarAI operates within the following emotional and relational themes:

- عشق (love)
- وصال (union)
- فراق (separation)
- شکایت (complaint / grievance)

If a user question is ambiguous, the system assumes it is about **یار** (the beloved / partner).

---

## Repository Contents

This repository currently contains **static, canonical resources** used by the system:

- `interpretation_templates.json`  
  Templates that guide the tone and structure of modern Persian interpretations.

- `theme_tone_table.md`  
  Documentation of how themes map to interpretive tone and style.

- `LICENSE`  
  Project license.

Code, datasets, and annotation pipelines are being re-introduced incrementally and intentionally.

---

## Project Status

This repository is under active development.

The current focus is on:
- stabilizing semantic definitions
- validating annotation guidelines
- establishing clean version-control practices

Executable code and datasets will be added in subsequent phases.

---

## Disclaimer

YaarAI is a literary and cultural exploration project.  
It does not provide fortune-telling, life advice, or predictive guarantees.
