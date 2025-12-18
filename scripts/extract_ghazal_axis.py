# scripts/extract_ghazal_axis.py
# Extract ghazal-level semantic axis (v1.0)
# Rate-limit safe

import json
import time
from collections import defaultdict
from pathlib import Path

from openai import OpenAI, RateLimitError

from prompts.prompts_v1 import (
    SYSTEM_PROMPT,
    GHAZAL_AXIS_PROMPT,
    PROMPT_VERSION,
)

MODEL_NAME = "gpt-4.1"

RAW_PATH = Path("data/raw/ghazals_with_insight.jsonl")
OUT_PATH = Path("data/annotations/ghazal_axis_v1.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

client = OpenAI()


def load_existing_poem_ids(path: Path) -> set[int]:
    """Return poem_ids already processed (resume-safe)."""
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return {json.loads(line)["poem_id"] for line in f}


def load_raw_data() -> list[dict]:
    with RAW_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def call_gpt_with_backoff(prompt: str) -> str:
    """Call GPT-4.1 with simple rate-limit backoff."""
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                top_p=1.0,
                seed=42,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            wait_time = 1.0
            print(f"[RATE LIMIT] sleeping {wait_time}s...")
            time.sleep(wait_time)


def main():
    rows = load_raw_data()
    done_poems = load_existing_poem_ids(OUT_PATH)

    poems = defaultdict(list)
    for r in rows:
        poems[r["poem_id"]].append(r)

    with OUT_PATH.open("a", encoding="utf-8") as out:
        for poem_id, bayts in poems.items():
            if poem_id in done_poems:
                continue

            all_bayts_text = "\n".join(
                f"- {b['text']}" for b in bayts
            )

            ghazal_prose = bayts[0]["insight"]["ghazal_summary"]

            prompt = GHAZAL_AXIS_PROMPT.format(
                all_bayts=all_bayts_text,
                ghazal_prose=ghazal_prose,
            )

            axis = call_gpt_with_backoff(prompt)

            record = {
                "poem_id": poem_id,
                "ghazal_axis": axis,
                "annotation_meta": {
                    "model": MODEL_NAME,
                    "prompt_version": PROMPT_VERSION,
                },
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()

            print(f"[OK] poem_id={poem_id} → {axis}")

            # gentle smoothing to stay under TPM
            time.sleep(0.2)


if __name__ == "__main__":
    main()
