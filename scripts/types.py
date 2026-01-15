# scripts/types.py
from typing import List, Optional, TypedDict


class BeytRow(TypedDict):
    poem_id: int
    beyt_id: int
    text: str                 # full beyt (couplet)
    affect: List[str]         # may be empty
    lens: Optional[str]       # None or lens label
