from __future__ import annotations
from dataclasses import dataclass
from agent.harness.schema import validate_schema
from agent.harness.privacy import privacy_issues
from agent.harness.provenance import validate_provenance

@dataclass
class HarnessResult:
    status: str
    errors: list[str]
    score: int


def confidence_score(entity, independent_sources: int = 0, official_confirmed: bool = False, relation_confirmed: bool = False, location_confirmed: bool = False, relevance_clear: bool = False) -> int:
    score = 0
    if official_confirmed: score += 30
    if independent_sources >= 1: score += 20
    if relation_confirmed: score += 20
    if location_confirmed: score += 15
    if relevance_clear: score += 15
    return min(score, 100)


def evaluate(entity, duplicate_status: str = "NEW", independent_sources: int = 0, official_confirmed: bool = False, relation_confirmed: bool = False, location_confirmed: bool = False, relevance_clear: bool = False) -> HarnessResult:
    errors = validate_schema(entity) + privacy_issues(entity) + validate_provenance(entity)
    score = confidence_score(entity, independent_sources, official_confirmed, relation_confirmed, location_confirmed, relevance_clear)
    if duplicate_status in {"EXISTING", "MERGE_REVIEW", "POSSIBLE_DUPLICATE"}:
        errors.append(f"duplicate status: {duplicate_status}")
    if errors:
        status = "REJECTED" if any("missing" in e or "invalid" in e or "privacy" in e.lower() for e in errors) else "NEEDS_REVIEW"
    else:
        status = "CONFIRMED" if score >= 80 and official_confirmed else "NEEDS_REVIEW"
    return HarnessResult(status, errors, score)
