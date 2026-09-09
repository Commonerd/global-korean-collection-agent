# Global Korean Business & Diaspora Autonomous Collection Agent

Google Spreadsheet를 최종 저장소로 사용하는 자율형 글로벌 한인 데이터 수집·검증 에이전트입니다.

이 구현은 `SYSTEM_DESIGN.md`의 핵심 원칙을 반영합니다.

- AI/탐색 결과를 그대로 저장하지 않고 **Candidate → Verification → Harness → Approved Entity → Sheet Write** 순으로 통제
- Google Sheet를 기존 DB/최종 저장소로 사용
- SQLite로 Agent State + Candidate + Graph + Seed를 영속화
- Region / Entity / Relation / Gap Seed를 이용한 반복 탐색 Loop
- deterministic duplicate / URL / 좌표 / 개인정보 / provenance 검사
- 공식 출처 우선 검증 및 confidence 보조 점수
- `DRY_RUN=true`를 기본값으로 하여 실제 Sheet 변경을 막음
- 검색/Places/LLM 공급자를 Adapter로 분리
- Google Places 결과의 공식 website를 직접 조사하고, 페이지의 명시된 JSON-LD 관계를 Candidate와 Graph로 확장
- 저장된 Seed를 우선순위에 따라 재탐색하고 depth·request·entity·runtime 예산으로 종료
- 외부 API가 없어도 Mock adapter로 end-to-end 테스트 가능

## 빠른 시작

### 1. Python 환경

Python 3.9+ 권장.

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. 설정 파일

```bash
cp .env.example .env
```

처음에는 다음 상태로 실행하는 것을 권장합니다.

```env
MODE=mock
DRY_RUN=true
```

### 3. Mock 전체 Loop 실행

```bash
python -m agent.main --mode once
```

상태 확인:

```bash
python -m agent.main --mode status
```

테스트:

```bash
pytest -q
```

## 실제 Google Sheets 연결

Google Sheets API를 활성화하고 서비스 계정 또는 ADC(Application Default Credentials)를 준비한 뒤, 기존 Spreadsheet를 서비스 계정 이메일과 공유합니다.

`.env` 예:

```env
MODE=production
DRY_RUN=true
GOOGLE_SPREADSHEET_ID=여기에_스프레드시트_ID
GOOGLE_SHEET_NAME=Sheet1
GOOGLE_SERVICE_ACCOUNT_JSON=/absolute/path/service-account.json
```

`DRY_RUN=true`에서는 읽기/검증/계획은 진행하지만 실제 append/update는 수행하지 않습니다. 최초 운영에서는 반드시 dry-run으로 결과를 확인한 뒤 `DRY_RUN=false`로 전환하세요.

Google Sheets API는 `spreadsheets.values.get/append/update` 같은 값 읽기·쓰기 메서드를 제공합니다. 구현은 헤더 행을 먼저 읽고 실제 컬럼명에 매핑하도록 되어 있습니다.

## 선택적 검색 / Places / LLM

### Google Places API (New)

```env
GOOGLE_PLACES_API_KEY=...
ENABLE_PLACES=true
```

현재 구현은 Places API (New)의 `places:searchText` REST endpoint를 사용합니다. FieldMask를 명시하고, 결과는 Candidate로 변환됩니다. Places 결과에 website가 있으면 `WebPageAdapter`로 직접 열고, 페이지의 JSON-LD에 명시된 `brand`, `parentOrganization`, `manufacturer`, `department`, `subOrganization` 등의 관계만 추가 Candidate로 확장합니다. 원본 페이지 URL은 provenance로 보존됩니다.

### Google Custom Search JSON API

```env
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_CX=...
ENABLE_WEB_SEARCH=true
```

production에서 CSE가 설정되지 않으면 `MockSearchAdapter`를 사용하지 않습니다. 검색 기능은 `SEARCH_UNAVAILABLE`로 기록하고, Google Places 결과와 공식 website 직접 조사만 계속합니다. Mock 검색은 `MODE=mock`일 때만 사용합니다.

### Relation Expansion

한 번의 `once` 실행에서도 다음 경로가 동작합니다.

```text
Google Places
  -> official website
  -> explicit JSON-LD related entity
  -> Candidate / Verification / Duplicate / Harness
  -> Graph edge
  -> CONFIRMED + NEW만 Sheet append
  -> RELATION_SEED / ENTITY_SEED
```

관계가 명시되지 않은 이름이나 지점은 추측하여 생성하지 않습니다. 기존 Entity와 중복이면 새 Sheet row를 append하지 않습니다.

### Seed 재탐색

확장으로 생성된 `ENTITY_SEED`와 `RELATION_SEED`를 SQLite에 저장하고, 다음 iteration에서 priority가 높은 순서로 재실행합니다. Seed 상태는 `PENDING → RUNNING → DONE`으로 기록하며, 예산으로 중단되면 `FAILED`로 남깁니다. `MAX_DEPTH`, 요청 수, 신규 Entity 수, 실행 시간 제한과 query 방문 기록으로 무한 반복을 막습니다.

### LLM

선택 사항입니다. OpenAI 호환 API 또는 Ollama를 지원합니다.

```env
LLM_PROVIDER=none
# openai-compatible 사용 시
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
# Ollama 사용 시
# LLM_PROVIDER=ollama
# LLM_BASE_URL=http://localhost:11434
# LLM_MODEL=...
```

LLM은 사실 생성기가 아니라 **추출/요약 보조기**로만 사용하며, provenance 없는 주장은 Harness에서 저장 승인하지 않습니다.

## 운영 명령

단일 Loop:

```bash
python -m agent.main --mode once
```

여러 iteration:

```bash
python -m agent.main --mode loop --iterations 10
```

`loop`는 저장된 pending Seed를 다음 iteration의 입력으로 사용하고, `once`는 한 번의 bounded run만 수행합니다.

### 실행 방법

#### 1회 실행

원하는 목표를 한 번 오래 탐색합니다.

```bash
make collect-once GOAL="Osaka Korean restaurant"
```

기존 Sheet에는 `CONFIRMED + NEW`만 append됩니다.

#### 매일 오전 8시 실행

아래 한 줄로 macOS 스케줄러를 등록합니다.

```bash
make schedule-daily
```

매일 다음 4개 영역을 각각 탐색합니다.

```text
Korean restaurant overseas
Korean market overseas
Korean company overseas
Korean association overseas
```

각 영역은 3 iterations, 최대 3분으로 제한되며 pending Seed를 이어서 처리합니다. 결과 로그는 `data/logs/`에 저장됩니다. 최초 등록 전에는 `.env`의 `DRY_RUN=true`로 점검하세요.

수동 장시간 실행이 필요하면 `make long-loop GOAL="Osaka Korean restaurant"`를 사용합니다.

API key와 서비스 계정 정보는 plist에 넣지 않고 `.env`에서 관리합니다.

특정 목표:

```bash
python -m agent.main --mode once --goal "Tokyo Korean restaurant"
```

후보 검토 큐 보기:

```bash
python -m agent.main --mode review
```

Sheet 연결 확인:

```bash
python -m agent.main --mode schema
```

## 디렉터리

```text
agent/
├── main.py
├── config.py
├── adapters/
│   ├── sheets.py
│   ├── search.py
│   ├── places.py
│   ├── web.py
│   └── llm.py
├── agents/
│   ├── discovery.py
│   ├── verification.py
│   ├── resolution.py
│   └── planner.py
├── loop/
│   ├── engine.py
│   ├── policy.py
│   └── scheduler.py
├── graph/
│   ├── model.py
│   ├── store.py
│   └── traversal.py
├── harness/
│   ├── schema.py
│   ├── duplicate.py
│   ├── privacy.py
│   ├── provenance.py
│   └── evaluator.py
├── models/
│   ├── entity.py
│   ├── candidate.py
│   └── seed.py
└── state/
    └── store.py
```

## 데이터 흐름

```text
Existing Sheet
  ↓
Coverage / State
  ↓
Planner
  ↓
Search / Places
  ↓
Candidate
  ↓
Investigation / Verification
  ↓
Entity Resolution
  ↓
Harness
  ├─ accepted
  ├─ review
  └─ rejected
  ↓
Graph update
  ↓
Approved Entity only
  ↓
Google Sheet append/update
  ↓
new Seeds
  ↓
next Loop
```

## 안전 설계

- 기본 `DRY_RUN=true`
- `MAX_DEPTH`, `MAX_REQUESTS_PER_RUN`, `MAX_REQUESTS_PER_DOMAIN`, `MAX_NEW_ENTITIES_PER_RUN`, `MAX_RUNTIME_SECONDS`, `MAX_RETRIES` 제한
- query / URL / entity 중복 방문 방지
- 실패 도메인 backoff
- 개인 연락처/자택 주소/리뷰 작성자 등 개인정보 필터
- provenance가 없는 entity는 승인하지 않음
- 기존 Sheet 행을 자동 덮어쓰지 않으며 기본 동작은 append
- production에서는 `CONFIRMED`이면서 `NEW`인 Entity만 append
- 빈 Sheet 탭은 기존 행이 없을 때만 canonical header를 최초 1회 생성
- 신규 기록에는 `discoveryMethod`, `sourceEntityId`, `relationType`, `sourceSeed`를 자동 기록
- 모든 실행 로그를 `data/logs/agent.log`에 append하고 화면에도 출력
- duplicate가 애매하면 `MERGE_REVIEW`

## 기존 Sheet 스키마

기본 Writer는 첫 행을 헤더로 읽고 다음 canonical field를 가능한 컬럼명에 매핑합니다.

```text
id, name, nameKo, nameEn, entityType, category,
country, city, address, latitude, longitude,
website, phone, placeId, koreanRelevance,
parentEntityId, verificationStatus, confidenceScore,
provenance, discoveryMethod, sourceEntityId, relationType,
sourceSeed, discoveredAt, updatedAt
```

`discoveryMethod`는 `PLACES`, `OFFICIAL_WEB`, `SEARCH` 중 하나이며, 관계 확장 행에는 원본 Entity와 관계 타입, Seed가 함께 기록됩니다. 새 컬럼은 기존 행을 덮어쓰지 않고 헤더에만 추가됩니다.

기존 DB의 컬럼명이 다르면 `config/column_map.json`에서 추가 별칭을 지정할 수 있습니다.

## Review Queue

자동 확정하지 못한 후보는 SQLite의 review queue에 남습니다.

```text
NEEDS_REVIEW
MERGE_REVIEW
REJECTED
```

검토 큐의 목적은 AI가 사람을 대체하는 것이 아니라, **불확실한 데이터가 기존 DB로 침투하는 것을 막는 것**입니다.

## 출처

이 프로젝트의 설계 기준은 함께 제공된 `SYSTEM_DESIGN.md`입니다. Google Sheets 값 API 및 Places API(New)의 현재 공식 문서 확인을 바탕으로 REST adapter를 작성했습니다.

- Google Sheets API values: https://developers.google.com/workspace/sheets/api/guides/values
- Google Places API (New) Text Search: https://developers.google.com/maps/documentation/places/web-service/text-search


https://chatgpt.com/c/6aa02a11-c000-83e9-8f14-e502b2705c46