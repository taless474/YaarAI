# scripts/extract_bayt_annotations.py
# Extract bayt-level semantic annotations (v1.0)
# Rate-limit safe + resume-safe + strict affect validation with rejection logging

import json
import time
from pathlib import Path
from datetime import datetime

from openai import OpenAI, RateLimitError

from prompts.prompts_v1 import (
    SYSTEM_PROMPT,
    BAYT_PROMPT,
    PROMPT_VERSION,
)

MODEL_NAME = "gpt-4.1"

AFFECT_VOCAB = [
    "اندوه",
    "امید",
    "ناامیدی",
    "حیرت",
    "شوق",
    "حسرت",
    "آرامش",
    "بی‌قراری",
]

RAW_PATH = Path("data/raw/ghazals_with_insight.jsonl")
AXIS_PATH = Path("data/annotations/ghazal_axis_v1.jsonl")
OUT_PATH = Path("data/annotations/bayt_annotations_v1.jsonl")

# NEW: rejection log
REJECT_LOG_PATH = Path("data/logs/rejected_affects_v1.jsonl")
REJECT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

client = OpenAI()


def load_axis_map() -> dict:
    """Map poem_id -> ghazal_axis"""
    axis_map = {}
    with AXIS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            axis_map[r["poem_id"]] = r["ghazal_axis"]
    return axis_map


def load_done_keys() -> set[tuple]:
    """Return (poem_id, bayt_id) already processed."""
    if not OUT_PATH.exists():
        return set()
    done = set()
    with OUT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            done.add((r["poem_id"], r["bayt_id"]))
    return done


def call_gpt_with_backoff(prompt: str) -> dict:
    """Call GPT-4.1 and return parsed JSON with retry on rate limit."""
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
            content = response.choices[0].message.content
            return json.loads(content)

        except RateLimitError:
            wait_time = 1.0
            print(f"[RATE LIMIT] sleeping {wait_time}s...")
            time.sleep(wait_time)

        except json.JSONDecodeError:
            print("[WARN] Invalid JSON, retrying...")
            time.sleep(0.5)


def validate_annotation(obj: dict):
    """Raise AssertionError if annotation is invalid."""
    assert isinstance(obj, dict)
    assert "bayt_hint" in obj
    assert "affect" in obj
    assert isinstance(obj["bayt_hint"], str)
    assert isinstance(obj["affect"], list)
    assert len(obj["affect"]) <= 2
    for a in obj["affect"]:
        assert a in AFFECT_VOCAB


def call_gpt_until_valid(prompt: str, meta: dict, max_attempts: int = 2) -> dict:
    """
    Call GPT up to `max_attempts`.
    If affect is invalid after final attempt, return blank affect [].
    All rejections are logged.
    """
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        annotation = call_gpt_with_backoff(prompt)

        try:
            validate_annotation(annotation)
            return annotation

        except AssertionError:
            rejected = {
                "timestamp": datetime.utcnow().isoformat(),
                "poem_id": meta["poem_id"],
                "bayt_id": meta["bayt_id"],
                "attempt": attempt,
                "returned_affect": annotation.get("affect"),
                "allowed_affect_vocab": AFFECT_VOCAB,
                "model": MODEL_NAME,
                "prompt_version": PROMPT_VERSION,
                "final": attempt == max_attempts,
            }

            with REJECT_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rejected, ensure_ascii=False) + "\n")

            print(
                f"[REJECT] poem_id={meta['poem_id']} "
                f"bayt_id={meta['bayt_id']} "
                f"attempt={attempt} "
                f"affect={annotation.get('affect')}"
            )

            time.sleep(0.3)

    # ⬇️ Final fallback after max_attempts
    print(
        f"[BLANK] poem_id={meta['poem_id']} "
        f"bayt_id={meta['bayt_id']} affect=[]"
    )

    return {
        "bayt_hint": annotation.get("bayt_hint", "").strip(),
        "affect": [],
    }



def main():
    axis_map = load_axis_map()
    done = load_done_keys()

    with RAW_PATH.open("r", encoding="utf-8") as fin, \
         OUT_PATH.open("a", encoding="utf-8") as fout:

        for line in fin:
            row = json.loads(line)
            key = (row["poem_id"], row["bayt_id"])

            if key in done:
                continue

            prompt = BAYT_PROMPT.format(
                affect_list="، ".join(AFFECT_VOCAB),
                ghazal_axis=axis_map[row["poem_id"]],
                bayt_text=row["text"],
                bayt_prose=row["insight"]["bayt_summary"],
            )

            annotation = call_gpt_until_valid(
                prompt,
                meta={
                    "poem_id": row["poem_id"],
                    "bayt_id": row["bayt_id"],
                },
            )

            record = {
                "poem_id": row["poem_id"],
                "bayt_id": row["bayt_id"],
                "bayt_hint": annotation["bayt_hint"],
                "affect": annotation["affect"],
                "ghazal_axis": axis_map[row["poem_id"]],
                "annotation_meta": {
                    "model": MODEL_NAME,
                    "prompt_version": PROMPT_VERSION,
                },
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            fout.flush()

            print(f"[OK] poem_id={row['poem_id']} bayt_id={row['bayt_id']}")

            time.sleep(0.25)


if __name__ == "__main__":
    main()
