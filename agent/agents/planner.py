from __future__ import annotations
from collections import Counter
from agent.models.seed import Seed
import hashlib

DEFAULT_CATEGORIES = ["restaurant", "market", "service", "corporate office", "organization"]


def make_seed(seed_type: str, query: str, priority: float, depth: int, context=None) -> Seed:
    sid = hashlib.sha1(f"{seed_type}|{query}".encode()).hexdigest()[:16]
    return Seed(seedId=sid, seedType=seed_type, query=query, priority=priority, depth=depth, context=context or {})


def coverage_seeds(existing: list[dict]) -> list[Seed]:
    counts = Counter((e.get("city") or "unknown", e.get("category") or "unknown") for e in existing)
    if not counts:
        return [make_seed("REGION_SEED", "Tokyo Korean business", 100, 0), make_seed("REGION_SEED", "Osaka Korean business", 90, 0)]
    cities = sorted({e.get("city") for e in existing if e.get("city")}) or ["Tokyo", "Osaka"]
    seeds=[]
    for city in cities[:10]:
        for cat in DEFAULT_CATEGORIES:
            n=counts[(city,cat)]
            if n == 0:
                seeds.append(make_seed("GAP_SEED", f"{city} Korean {cat}", 70, 0, {"city":city,"category":cat,"count":n}))
    return sorted(seeds, key=lambda s:s.priority, reverse=True)
