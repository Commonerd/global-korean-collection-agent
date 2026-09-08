from __future__ import annotations
import hashlib
from agent.models.candidate import Candidate


def candidate_from_result(result: dict, discovered_from: str) -> Candidate:
    raw = f"{result.get('name','')}|{result.get('address','')}|{result.get('website','')}|{result.get('placeId','')}"
    cid = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return Candidate(
        candidateId=cid,
        rawName=result.get("name"),
        rawAddress=result.get("address"),
        discoveredFrom=discovered_from,
        sourceUrls=[u for u in [result.get("website"), result.get("sourceUrl")] if u],
        extractedData=result,
    )
