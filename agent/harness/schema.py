from __future__ import annotations
from urllib.parse import urlparse


def validate_schema(entity) -> list[str]:
    errors = []
    if not entity.name.strip(): errors.append("empty name")
    if not entity.entityType: errors.append("missing entityType")
    if entity.latitude is not None and not -90 <= entity.latitude <= 90: errors.append("invalid latitude")
    if entity.longitude is not None and not -180 <= entity.longitude <= 180: errors.append("invalid longitude")
    if entity.website:
        try:
            parsed = urlparse(entity.website)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append("invalid website URL")
        except Exception:
            errors.append("invalid website URL")
    return errors
