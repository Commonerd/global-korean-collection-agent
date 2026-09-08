# 설치 및 사용 설명서

## 1. 무엇이 구현되어 있나

이 프로젝트는 제공된 설계 문서의 다음 계층을 실제 코드로 구현했습니다.

1. 기존 DB 상태 읽기
2. Coverage 기반 Seed 생성
3. Search / Places Adapter
4. Candidate Extraction
5. Web 조사
6. Verification / Provenance
7. Entity Resolution
8. Harness
9. SQLite Agent State
10. 내부 Graph(Node/Edge)
11. Review Queue
12. Approved Entity만 Google Sheet 기록
13. 새 Entity/Relation Seed 생성
14. 반복 Loop 및 종료 제한

초기 구현에서 GIS/UI/Neo4j/PostGIS/Redis/Kubernetes는 넣지 않았습니다.

## 2. 권장 설치

```bash
cd global-korean-collection-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3. 반드시 먼저 Mock 실행

```bash
python -m agent.main --mode once --goal "Tokyo Korean restaurant"
```

상태:

```bash
python -m agent.main --mode status
```

테스트:

```bash
pytest -q
```

Mock은 외부 API를 호출하지 않으며, `example.com` 형태의 모의 근거로 전체 파이프라인을 시험합니다.

## 4. Google Sheets 연결

### Google Cloud

프로젝트를 만든 뒤 Google Sheets API를 활성화합니다.

서비스 계정 방식을 쓰려면 서비스 계정 JSON을 내려받고, 그 서비스 계정 이메일을 기존 코리아타운DB Spreadsheet에 편집자로 공유합니다.

`.env`:

```env
MODE=production
GOOGLE_SPREADSHEET_ID=YOUR_ID
GOOGLE_SHEET_NAME=Sheet1
GOOGLE_SERVICE_ACCOUNT_JSON=/absolute/path/service-account.json
DRY_RUN=true
```

먼저:

```bash
python -m agent.main --mode once --goal "Tokyo Korean restaurant"
```

실제 쓰기 전에 `DRY_RUN=true`로 review queue와 log를 확인합니다.

실제 추가를 허용:

```env
DRY_RUN=false
```

다시 한 번 실행합니다.

## 5. 기존 Sheet 스키마가 다른 경우

첫 행의 header를 읽어서 canonical field에 매핑합니다. 추가 컬럼 별칭은 `config/column_map.json`에 정의합니다.

주의: 현재 샘플 Writer는 **append 중심**입니다. 기존 행 update는 의도적으로 `NotImplementedError`를 발생시키므로, 실제 DB의 고유 키와 컬럼 구조를 확인한 뒤 별도 구현하는 것이 안전합니다.

## 6. Google Places API 추가

Places API (New)의 Text Search를 사용합니다.

```env
ENABLE_PLACES=true
GOOGLE_PLACES_API_KEY=YOUR_KEY
```

운영 시 API key restriction과 billing/usage policy를 확인하세요.

## 7. 검색 API

Google Custom Search JSON API를 사용할 수 있습니다.

```env
ENABLE_WEB_SEARCH=true
GOOGLE_CSE_API_KEY=YOUR_KEY
GOOGLE_CSE_CX=YOUR_CX
```

검색 결과는 최종 엔티티가 아니라 Candidate로만 들어갑니다.

## 8. LLM

처음에는 LLM 없이 돌리는 것을 권장합니다.

```env
LLM_PROVIDER=none
```

필요할 때 OpenAI-compatible endpoint 또는 Ollama를 붙일 수 있습니다. 현재 Loop 핵심은 LLM이 없어도 deterministic으로 작동합니다.

LLM을 붙이더라도 역할은 후보 추출/요약 보조입니다. 근거가 없는 사실은 승인 대상이 아닙니다.

## 9. 운영

단일 Loop:

```bash
python -m agent.main --mode once
```

10 iterations:

```bash
python -m agent.main --mode loop --iterations 10
```

특정 Seed:

```bash
python -m agent.main --mode once --goal "Osaka Korean corporate offices"
```

Review Queue:

```bash
python -m agent.main --mode review
```

기존 Sheet의 첫 행/데이터가 읽히는지 확인하려면:

```bash
python -m agent.main --mode schema
```

## 10. 안전 한도

`.env`에서 다음을 조절할 수 있습니다.

```env
MAX_DEPTH=3
MAX_REQUESTS_PER_RUN=30
MAX_REQUESTS_PER_DOMAIN=8
MAX_NEW_ENTITIES_PER_RUN=10
MAX_RUNTIME_SECONDS=300
MAX_RETRIES=2
```

이 한도는 무한 재귀 탐색, 동일 URL 반복, 과도한 API 사용을 막기 위한 것입니다.

## 11. 실제 운영 전에 확인할 것

- 기존 Sheet의 실제 컬럼명을 `column_map.json`과 일치시키기
- 공식 출처 도메인 정책 정교화
- Google Places/검색 API의 실제 quota 확인
- robots.txt / 이용약관 검토
- 개인정보 필터를 실제 수집 범위에 맞게 강화
- `update_entity()` 구현 전에 기존 DB 백업
- first run은 dry-run
- Review Queue에서 false positive 확인

## 12. 시스템의 최종 원칙

AI가 발견한 내용을 바로 Sheet에 쓰지 않습니다.

```text
AI / Search
  ↓
Candidate
  ↓
Verification + Provenance
  ↓
Entity Resolution
  ↓
Harness
  ↓
CONFIRMED
  ↓
Google Sheet
```

이는 제공된 설계 문서의 핵심 원칙인 **“AI는 탐색하고, 코드가 저장을 통제한다”**를 코드 구조에 반영한 것입니다.
