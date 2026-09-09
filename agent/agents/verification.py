from __future__ import annotations
from urllib.parse import urlparse
from agent.models.entity import Provenance


def verify_candidate(candidate, fetched_pages: list[dict]) -> dict:
    sources = []
    # A Google Places result is an authoritative directory record even when the
    # business website is unavailable or is not on a recognized corporate domain.
    official = bool(candidate.extractedData.get("placeId") or candidate.extractedData.get("_source_type") == "official_web")
    independent = 0
    location_confirmed = bool(candidate.extractedData.get("address"))
    relevance_clear = bool(candidate.extractedData.get("koreanRelevance"))
    for page in fetched_pages:
        url = page.get("url")
        title = page.get("title") or "Web page"
        if not url:
            continue
        host = urlparse(url).netloc.lower()
        is_official = candidate.extractedData.get("_source_type") == "official_web" or any(x in host for x in [".kr", "samsung.com", "lg.com", "hyundai.com"])
        if is_official:
            official = True
        else:
            independent += 1
        sources.append(Provenance(sourceName=title, sourceUrl=url, sourceType="official" if is_official else "web", verificationMethod="page_fetch", evidence=(page.get("text") or "")[:500]))
    return {
        "provenance": sources,
        "official_confirmed": official,
        "independent_sources": min(independent, 3),
        "location_confirmed": location_confirmed,
        "relevance_clear": relevance_clear,
    }
