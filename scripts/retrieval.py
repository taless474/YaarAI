# scripts/retrieval.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class RetrievalConfig:
    model_name: str = "BAAI/bge-m3"
    temperature: float = 7.0
    floor: float = 0.85


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "data" / "datasets" / "beyts_canonical_v1.jsonl"
EMB_PATH = REPO_ROOT / "data" / "embeddings" / "beyts_embeddings.npy"


def load_beyts(dataset_path: Path = DATASET_PATH) -> list[dict]:
    beyts: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            beyts.append(json.loads(line))
    return beyts


def load_embeddings(emb_path: Path = EMB_PATH) -> np.ndarray:
    if not emb_path.exists():
        raise FileNotFoundError(
            f"Embeddings not found: {emb_path}\n"
            "Run: python -m scripts.embed_beyts"
        )
    emb = np.load(emb_path)
    if emb.ndim != 2:
        raise ValueError(f"Expected 2D embeddings array, got shape {emb.shape}")
    return emb.astype(np.float32, copy=False)


def fal_weights(similarities: np.ndarray, temperature: float = 7.0, floor: float = 0.85) -> np.ndarray:
    """
    Convert cosine similarities into VERY WEAK sampling weights.

    - No truncation (no top-K)
    - No thresholds
    - High temperature + floor keeps Fal-ness (tilt, not select)
    """
    sim = similarities.astype(np.float64, copy=False)

    # normalize to [0, 1]
    sim = sim - sim.min()
    denom = sim.max() + 1e-12
    sim = sim / denom

    # flatten aggressively
    sim = np.power(sim, 1.0 / float(temperature))

    # add floor so nothing is excluded
    weights = float(floor) + (1.0 - float(floor)) * sim

    # normalize
    weights = weights / weights.sum()
    return weights.astype(np.float64, copy=False)


class FalRetriever:
    def __init__(
        self,
        beyts: list[dict],
        embeddings: np.ndarray,
        config: RetrievalConfig = RetrievalConfig(),
    ) -> None:
        if len(beyts) != embeddings.shape[0]:
            raise ValueError(
                f"Dataset/embedding mismatch: {len(beyts)} rows vs {embeddings.shape[0]} embeddings. "
                "Rebuild embeddings if dataset changed."
            )
        self.beyts = beyts
        self.embeddings = embeddings
        self.config = config
        self.model = SentenceTransformer(config.model_name)

    def draw(self, question: str, seed: Optional[int] = None) -> dict:
        q_vec = self.model.encode([question], normalize_embeddings=True)[0].astype(np.float32, copy=False)
        sims = self.embeddings @ q_vec  # cosine since normalized
        weights = fal_weights(sims, temperature=self.config.temperature, floor=self.config.floor)

        rng = np.random.default_rng(seed)
        idx = int(rng.choice(len(self.beyts), p=weights))
        return self.beyts[idx]

    def draw_many(self, question: str, n: int = 3, seed: Optional[int] = None) -> list[dict]:
        # Seeded run: stable sequence; unseeded: random each call
        rng = np.random.default_rng(seed)

        q_vec = self.model.encode([question], normalize_embeddings=True)[0].astype(np.float32, copy=False)
        sims = self.embeddings @ q_vec
        weights = fal_weights(sims, temperature=self.config.temperature, floor=self.config.floor)

        idxs = rng.choice(len(self.beyts), size=n, replace=True, p=weights)
        return [self.beyts[int(i)] for i in idxs]


def build_default_retriever(config: RetrievalConfig = RetrievalConfig()) -> FalRetriever:
    beyts = load_beyts()
    emb = load_embeddings()
    return FalRetriever(beyts=beyts, embeddings=emb, config=config)
