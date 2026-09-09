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

# Production write and relation expansion

Implemented the production Google Places -> Web -> Relation -> Sheets flow.

## Code changes

- `agent/adapters/search.py`
	- Added `EmptySearchAdapter`.
	- Production no longer falls back to `MockSearchAdapter` when CSE is not configured.
- `agent/adapters/sheets.py`
	- Initializes headers only for an entirely empty Sheet tab.
	- Appends rows with the existing header mapping without deleting or overwriting existing rows.
	- Logs successful append operations.
- `agent/adapters/web.py`
	- Extracts and returns valid JSON-LD blocks from fetched pages.
- `agent/agents/discovery.py`
	- Converts explicitly declared JSON-LD organization, brand, branch, and related entity data into Candidates.
	- Preserves the originating page URL and relation metadata.
- `agent/agents/verification.py`
	- Treats Google Places `placeId` and official-web candidates as authoritative evidence.
- `agent/loop/engine.py`
	- Investigates Places-provided official websites during the run.
	- Emits `SEARCH_UNAVAILABLE`, Places, Web, extraction, resolution, verification, relation, write, and seed logs.
	- Processes expanded Candidates through the existing verification, duplicate, Harness, Graph, and Sheet paths.
	- Creates relation and entity seeds without enabling an unbounded autonomous loop.
	- Reuses fetched official-page evidence for expanded Candidates.
- `tests/test_harness.py`
	- Added regression coverage for Places verification and JSON-LD brand relation extraction.
- `README.md`, `SYSTEM_DESIGN.md`
	- Documented production search fallback behavior, official-web expansion, provenance, relation edges, seed creation, and safe Sheet append rules.

## Verification

- `python -m compileall -q agent tests` — PASS
- `pytest -q` — 5 passed
- Production one-shot execution confirmed:
	- Google Places discovery
	- official website investigation
	- related Candidate extraction
	- duplicate resolution and verification
	- Graph relation creation
	- safe Google Sheets append for `CONFIRMED + NEW`
	- new relation/entity seed creation
