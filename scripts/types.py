# scripts/types.py
from typing import List, Optional, TypedDict


class BaytRow(TypedDict):
    poem_id: int
    bayt_id: int
    text: str                 # full bayt (couplet)
    affect: List[str]         # may be empty
    lens: Optional[str]       # None or lens label
