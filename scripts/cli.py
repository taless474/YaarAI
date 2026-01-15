# scripts/cli.py
from __future__ import annotations

import argparse

from .retrieval import RetrievalConfig, build_default_retriever
from .fal_assembly import assemble_fal, set_interpret


def main() -> None:
    parser = argparse.ArgumentParser(description="YaarAI Fal (alignment-biased draw)")
    parser.add_argument("question", type=str, help="User question (Persian)")
    parser.add_argument("--n", type=int, default=1, help="Number of draws")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed")

    parser.add_argument("--temperature", type=float, default=7.0)
    parser.add_argument("--floor", type=float, default=0.85)

    parser.add_argument(
        "--no-interpret",
        action="store_true",
        help="Disable modern interpretation line (beyt-focused Fal)",
    )


    args = parser.parse_args()

    # Configure retriever (Fal core)
    config = RetrievalConfig(
        temperature=args.temperature,
        floor=args.floor,
    )
    retriever = build_default_retriever(config=config)

    # Configure presentation layer
    set_interpret(not args.no_interpret)

    # Draw Fal(s)
    beyts = retriever.draw_many(args.question, n=args.n, seed=args.seed)

    for i, beyt in enumerate(beyts, 1):
        print(f"\n--- Fal {i} ---")
        print(assemble_fal(beyt))


if __name__ == "__main__":
    main()
