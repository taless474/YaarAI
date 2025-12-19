# scripts/cli.py

import argparse
import numpy as np

from scripts.retrieval import (
    load_dataset,
    load_embeddings,
    retrieve_best_bayt,
)
from scripts.fal_assembly import assemble_fal
from scripts.language.affect_variants import AFFECT_VARIANTS
from scripts.language.lens_soft import LENS_VARIANTS_SOFT
from scripts.language.lens_hard import LENS_VARIANTS_HARD

# TEMP: stub until you plug a real embedder
def embed_query(text: str) -> np.ndarray:
    """
    Replace this with a real embedding model.
    For now, this is a placeholder.
    """
    raise NotImplementedError("Query embedding not wired yet.")


def main():
    parser = argparse.ArgumentParser(description="YaarAI Fal-e-Hafez CLI")
    parser.add_argument("query", type=str, help="User question (Persian)")
    args = parser.parse_args()

    rows = load_dataset()
    embeddings = load_embeddings()

    query_emb = embed_query(args.query)
    bayt_row = retrieve_best_bayt(
        query_emb,
        rows=rows,
        embeddings=embeddings,
    )

    out = assemble_fal(
        bayt_row,
        affect_variants=AFFECT_VARIANTS,
        lens_soft=LENS_VARIANTS_SOFT,
        lens_hard=LENS_VARIANTS_HARD,
    )

    print(out)


if __name__ == "__main__":
    main()
