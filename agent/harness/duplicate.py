from __future__ import annotations
from typing import Optional
from difflib import SequenceMatcher
import re


def _norm(value: Optional[str]) -> str:
    if not value: return ""
    return re.sub(r"[^a-z0-9가-힣]", "", value.lower())


def compare(candidate, existing_entities: list[dict]):
    c = candidate
    for e in existing_entities:
        if c.placeId and e.get("placeId") and c.placeId == e.get("placeId"):
            return "EXISTING", e
        if c.website and e.get("website") and c.website.rstrip("/").lower() == e.get("website", "").rstrip("/").lower():
            return "EXISTING", e
        if c.phone and e.get("phone") and c.phone == e.get("phone"):
            return "EXISTING", e
        score = SequenceMatcher(None, _norm(c.name), _norm(e.get("name"))).ratio()
        if score >= 0.92 and _norm(c.address) and _norm(c.address) == _norm(e.get("address")):
            return "POSSIBLE_DUPLICATE", e
        if score >= 0.96:
            return "MERGE_REVIEW", e
    return "NEW", None
