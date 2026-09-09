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


def extract_related_results(page: dict, parent_result: dict) -> list[dict]:
    """Extract only explicitly declared related entities from official JSON-LD."""
    raw_blocks = page.get("json_ld", [])
    results = []
    parent_name = (parent_result.get("name") or "").strip().lower()

    def nodes(value):
        if isinstance(value, list):
            for item in value:
                yield from nodes(item)
        elif isinstance(value, dict):
            if "@graph" in value:
                yield from nodes(value["@graph"])
            else:
                yield value

    def address_value(value):
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            return None
        return ", ".join(str(value.get(key)) for key in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry") if value.get(key)) or None

    for block in raw_blocks:
        for node in nodes(block):
            node_types = node.get("@type", [])
            if isinstance(node_types, str):
                node_types = [node_types]
            if not node.get("_relation") and not any(t in {"Organization", "Corporation", "Brand", "LocalBusiness", "Restaurant", "Place"} for t in node_types):
                continue
            name = node.get("name")
            if not isinstance(name, str) or not name.strip() or name.strip().lower() == parent_name:
                continue
            relation = "RELATED_TO"
            relation_value = node.get("_relation")
            if relation_value in {"parentOrganization", "brand", "manufacturer"}:
                relation = "OPERATED_BY" if relation_value == "parentOrganization" else "BRANCH_OF"
            result = {
                "name": name.strip(),
                "website": node.get("url") if isinstance(node.get("url"), str) else page.get("url"),
                "sourceUrl": page.get("url"),
                "address": address_value(node.get("address")),
                "phone": node.get("telephone"),
                "latitude": (node.get("geo") or {}).get("latitude") if isinstance(node.get("geo"), dict) else None,
                "longitude": (node.get("geo") or {}).get("longitude") if isinstance(node.get("geo"), dict) else None,
                "koreanRelevance": "official website related entity",
                "_relation_type": relation,
                "_source_type": "official_web",
            }
            results.append(result)
    return results


def related_results_from_json_ld(page: dict, parent_result: dict) -> list[dict]:
    """Expand declared organization, brand, and branch fields from JSON-LD."""
    results = []
    for block in page.get("json_ld", []):
        for node in _json_ld_nodes(block):
            for field in ("parentOrganization", "brand", "manufacturer", "department", "subOrganization"):
                value = node.get(field)
                values = value if isinstance(value, list) else [value]
                for related in values:
                    if isinstance(related, str):
                        related = {"name": related}
                    if not isinstance(related, dict):
                        continue
                    candidate = dict(related)
                    candidate["_relation"] = field
                    results.extend(extract_related_results({"url": page.get("url"), "json_ld": [candidate]}, parent_result))
    return results


def _json_ld_nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from _json_ld_nodes(item)
    elif isinstance(value, dict):
        if "@graph" in value:
            yield from _json_ld_nodes(value["@graph"])
        else:
            yield value
