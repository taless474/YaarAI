# scripts/retrieval.py

import json
import numpy as np
from pathlib import Path
from typing import List

from scripts.types import BaytRow

DATASET_PATH = Path("data/datasets/bayts_canonical_v1.jsonl")
EMBEDDINGS_PATH = Path("data/embeddings/bayts_embeddings.npy")

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_dataset() -> List[BaytRow]:
    rows = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_embeddings() -> np.ndarray:
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Embeddings not found at {EMBEDDINGS_PATH}. "
            "Run embedding pipeline first or use CLI demo mode."
        )
    return np.load(EMBEDDINGS_PATH)



def retrieve_best_bayt(
    query_embedding: np.ndarray,
    *,
    rows: List[BaytRow],
    embeddings: np.ndarray,
) -> BaytRow:
    sims = [cosine_sim(query_embedding, emb) for emb in embeddings]
    idx = int(np.argmax(sims))
    return rows[idx]
