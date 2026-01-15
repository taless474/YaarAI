# scripts/embed_beyts.py
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "data" / "datasets" / "beyts_canonical_v1.jsonl"
EMB_DIR = REPO_ROOT / "data" / "embeddings"
EMB_PATH = EMB_DIR / "beyts_embeddings.npy"

MODEL_NAME = "BAAI/bge-m3"


def load_beyts(dataset_path: Path) -> list[dict]:
    beyts: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            beyts.append(json.loads(line))
    return beyts


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    beyts = load_beyts(DATASET_PATH)
    texts = [b["text"] for b in beyts]

    print(f"Loaded {len(texts)} beyts from {DATASET_PATH}")
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("Encoding beyt texts (text-only) ...")
    emb = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )

    emb = np.asarray(emb, dtype=np.float32)
    if emb.ndim != 2 or emb.shape[0] != len(texts):
        raise RuntimeError(f"Unexpected embedding shape: {emb.shape}")

    EMB_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_PATH, emb)

    print(f"Saved embeddings: {EMB_PATH}")
    print(f"Shape: {emb.shape} dtype: {emb.dtype}")


if __name__ == "__main__":
    main()
