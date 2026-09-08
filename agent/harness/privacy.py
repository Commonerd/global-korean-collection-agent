from __future__ import annotations
import re

PRIVATE_PATTERNS = [
    r"\b(review(er)?|작성자|author)\b",
    r"\b(home address|자택|집 주소)\b",
    r"\b(personal email|개인 이메일)\b",
]


def privacy_issues(entity) -> list[str]:
    text = " ".join([
        entity.phone or "", entity.address or "", entity.koreanRelevance or ""
    ])
    return [p for p in PRIVATE_PATTERNS if re.search(p, text, flags=re.I)]
