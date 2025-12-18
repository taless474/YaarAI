# scripts/repair_bayt_hints.py
# Repair overlong or interpretive bayt_hints (v1.1)

import json
import time
from pathlib import Path

from openai import OpenAI, RateLimitError

from prompts.repair_prompts_v1 import (
    REPAIR_SYSTEM_PROMPT,
    REPAIR_BAYT_HINT_PROMPT,
)

MODEL_NAME = "gpt-4.1"

IN_PATH = Path("data/annotations/bayt_annotations_v1.jsonl")
OUT_PATH = Path("data/annotations/bayt_annotations_v1_1.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

RAW_PATH = Path("data/raw/ghazals_with_insight.jsonl")

client = OpenAI()


def load_raw_text():
    raw = {}
    with RAW_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            raw[(r["poem_id"], r["bayt_id"])] = r["text"]
    return raw


def call_gpt(prompt: str) -> str:
    while True:
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                top_p=1.0,
                seed=42,
            )
            return resp.choices[0].message.content.strip()
        except RateLimitError:
            time.sleep(1.0)


def main():
    raw_text = load_raw_text()

    done_keys = set()
    if OUT_PATH.exists():
        with OUT_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done_keys.add((r["poem_id"], r["bayt_id"]))

    with IN_PATH.open("r", encoding="utf-8") as fin, \
         OUT_PATH.open("a", encoding="utf-8") as fout:

        for line in fin:
            r = json.loads(line)
            key = (r["poem_id"], r["bayt_id"])

            if key in done_keys:
                continue

            old_hint = r["bayt_hint"]
            repaired = False
            new_hint = old_hint

            if len(old_hint.split()) > 8:
                prompt = REPAIR_BAYT_HINT_PROMPT.format(
                    bayt_text=raw_text[key],
                    old_hint=old_hint,
                )
                candidate = call_gpt(prompt)

                # accept only if genuinely shorter and non-empty
                if candidate and len(candidate.split()) < len(old_hint.split()):
                    new_hint = candidate
                    repaired = True

            out = dict(r)
            out["bayt_hint"] = new_hint
            out["annotation_meta"] = {
                **r.get("annotation_meta", {}),
                "repair": repaired,
                "repair_rule": "bayt_hint_len>8",
            }

            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            fout.flush()

            if repaired:
                print(f"[REPAIRED] {key}:")
                print("  old:", old_hint)
                print("  new:", new_hint)
            else:
                print(f"[KEPT] {key}")

            time.sleep(0.25)


if __name__ == "__main__":
    main()
