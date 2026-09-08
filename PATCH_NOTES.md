# Compatibility patch — macOS / Python 3.9

The initial package used Python 3.10+ features while the documented runtime was compatible with Python 3.9.

Fixed:
- `@dataclass(slots=True)` -> `@dataclass`
- PEP 604 annotations such as `str | None` -> `Optional[str]`
- Added missing `Dict` / `Optional` imports
- `pyproject.toml` now declares `requires-python = ">=3.9"`
- README and Korean installation guide now state Python 3.9+

Verified after patch:
- `python -m compileall -q agent tests` — PASS
- `pytest -q` — 3 passed
- Mock one-shot loop — PASS
