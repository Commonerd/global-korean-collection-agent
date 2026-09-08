def validate_provenance(entity) -> list[str]:
    errors = []
    if not entity.provenance:
        errors.append("missing provenance")
    for i, p in enumerate(entity.provenance):
        if not p.sourceName:
            errors.append(f"provenance[{i}] missing sourceName")
        if not p.sourceType:
            errors.append(f"provenance[{i}] missing sourceType")
    return errors
