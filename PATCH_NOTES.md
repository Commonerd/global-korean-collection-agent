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

# Seed priority and bounded re-exploration

3단계 구현:

- 저장된 `ENTITY_SEED`와 `RELATION_SEED`를 다음 iteration의 입력으로 연결
- `SeedQueue`에서 priority가 높은 Seed를 먼저 실행
- Seed 상태를 `PENDING → RUNNING → DONE`으로 기록
- 예산으로 중단된 Seed는 `FAILED`로 기록
- `MAX_DEPTH`와 query 방문 기록으로 중복·무한 재탐색 방지
- `once`는 bounded one-shot, `loop --iterations N`은 pending Seed를 재사용

검증:

- `python -m compileall -q agent tests` — PASS
- `pytest -q` — 7 passed

# Long-run scheduler

- `scripts/run_long_collection.sh`에 장시간 production 실행 프로파일 추가
- `make long-loop GOAL="..."`로 depth 4, 12 iterations, 30분 bounded 탐색 실행
- macOS `launchd/com.global-korean-collection-agent.plist.example` 추가
- launchd는 매일 08:00에 실행하며 로그를 `data/logs/`에 기록
- API key와 서비스 계정 정보는 plist에 저장하지 않고 `.env`에서 로드

# Simple execution commands

- 1회 실행: `make collect-once GOAL="Osaka Korean restaurant"`
- 매일 08:00 등록: `make schedule-daily`
- daily 탐색 축: restaurant, market, company, association

# Discovery provenance columns

- Entity와 Google Sheets에 `discoveryMethod`, `sourceEntityId`, `relationType`, `sourceSeed` 추가
- `PLACES`, `OFFICIAL_WEB`, `SEARCH` 출처를 신규 행에 자동 기록
- 기존 Sheet 행은 수정하지 않고, 기존 헤더 뒤에 provenance 컬럼만 안전하게 추가

# Persistent execution logs

- 기본 로그 디렉터리 `data/logs/` 및 append 파일 `agent.log` 추가
- 모든 CLI 실행에 `RUN_START` / `RUN_END` 기록
- 화면 출력과 파일 로그를 동시에 유지
- `LOG_DIR`, `LOG_FILE` 환경변수로 경로 변경 가능
- launchd stdout/stderr도 `data/logs/`에 저장

# Web expansion verification gate

- 공식 웹 JSON-LD 관계를 Harness의 `relation_confirmed` 입력에 연결
- 관계·공식 출처·주소·한국 관련성이 모두 확인된 웹 확장 Entity만 `CONFIRMED`
- 주소가 없는 웹 회사/브랜드 후보는 계속 `NEEDS_REVIEW`로 보호
