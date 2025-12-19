
# 🌙 YaarAI — Fal‑e‑Hafez (v1.0)

YaarAI is a **semantic Fal‑e‑Hafez system** focused on *recognition, restraint, and silence*.

The system **never generates poetry** and **never explains Hafez**.
It retrieves an **authentic Hafez bayt** and, only when justified, adds a **minimal orientation line**.

> اصل کار اینه: اگر چیزی برای گفتن نیست، بیت گویاست.

---

## ✨ What YaarAI Does

1. Accepts a short Persian question (usually about love / yaar).
2. Retrieves **one real Hafez bayt** from a canonical dataset.
3. Optionally adds:
   - an **Affect** (حال)
   - a **Lens** (orientation)
4. Outputs a compact Fal in a strict, deterministic format.

No advice.
No reassurance.
No interpretation of symbols.

---

## 🧠 Core Design Principles

- **Bayt is the oracle**
- Meaning is **never added**
- Silence is the default
- Orientation is rare and descriptive
- Randomness is *presentation‑only*, never semantic

---

## 📦 Project Structure

```text
YaarAI/
├── data/
│   ├── datasets/            # canonical bayt JSONL
│   └── embeddings/          # precomputed vectors (offline)
│
├── notebooks/               # exploration only (not imported)
│
├── scripts/
│   ├── language/
│   │   ├── affect_variants.py
│   │   ├── lens_soft.py
│   │   └── lens_hard.py
│   │
│   ├── config.py            # lens sets, defaults
│   ├── types.py             # BaytRow contract
│   ├── fal_assembly.py      # core Fal logic
│   ├── retrieval.py         # embedding‑based retrieval (offline)
│   ├── cli.py               # command‑line interface
│   └── test_fal.py          # sanity test
│
└── README.md
```

---

## 🧾 Data Contract

Each bayt is represented as:

```python
BaytRow = {
    "poem_id": int,
    "bayt_id": int,
    "text": str,          # full couplet
    "affect": list[str],  # may be empty
    "lens": str | None,
}
```

Embeddings are **not** part of this contract.
They belong strictly to retrieval.

---

## 🎭 Affect (حال)

Affect is descriptive only.

- Closed vocabulary (e.g. حسرت، بی‌قراری، اندوه، شوق، حیرت…)
- Short, modern Persian sentences
- One sentence per affect
- No directives, no therapy language

---

## 🔍 Lens (Orientation)

Lenses are **rare** and structural.

### Soft Lenses (lean, do not conclude)
- انتظار
- فاصله
- گلایه
- پذیرش
- حیرت معرفتی

### Hard Lenses (assertive, restrained)
- ریا
- ناپایداری جهان

Exactly **one** lens sentence may appear.

---

## 🧩 Assembly Contract

Output order is **always bayt‑first**.

| Case | Affect | Lens | Output |
|----|----|----|----|
| A | ✓ | ✗ | Bayt + Affect |
| B | ✓ | ✓ | Bayt + Affect + Lens |
| C | ✗ | ✗ | Bayt + **بیت گویاست** |
| D | ✗ | ✓ | Bayt + Lens |

If nothing fires, silence is explicit.

---

## ▶️ Running a Test

From the repo root:

```bash
python -m scripts.test_fal
```

This validates Fal assembly without retrieval.

---

## 🖥 CLI Usage

```bash
python -m scripts.cli "سؤال من"
```

At v1.0, the CLI supports:
- Fal assembly
- Dataset loading

Embedding‑based retrieval is wired but requires
precomputed vectors in `data/embeddings/`.

---

## 🚧 What v1.0 Freezes

Frozen:
- Fal assembly logic
- Affect & Lens language
- Output contract
- Bayt‑first rendering

Not frozen:
- Embedding model choice
- Retrieval strategy
- UI layer (CLI vs API)

---

## 📜 License

MIT (planned)

---

## 🌿 Closing Note

YaarAI is not a chatbot.
It is a **Fal engine**.

Sometimes it speaks.
Often, it stays quiet.

That quiet is intentional.
