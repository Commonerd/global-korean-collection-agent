# SYSTEM_DESIGN.md
# Global Korean Business & Diaspora Autonomous Collection Agent

## 0. 문서 목적

이 문서는 **기존 코리아타운DB의 Google Spreadsheet에 글로벌 한인 관련 데이터를 자동으로 수집·검증·정리·기록하는 시스템**의 구현 명세다.

중요: **이 프로젝트의 목표는 GIS 화면을 만드는 것이 아니다.**
GIS 표시와 사용자 서비스는 기존 **코리아타운DB**가 담당한다.

이 시스템의 목표는 다음 하나다.

> 웹과 외부 데이터에서 새로운 한인 관련 엔티티를 자율적으로 발견하고, 근거를 확인하고, 중복을 제거하고, 구조화한 뒤 Google Spreadsheet에 안전하게 기록한다.

---

# 1. 핵심 목표

시스템은 다음 과정을 반복한다.

```text
기존 DB 상태 확인
    ↓
수집 우선순위 결정
    ↓
Search / Places / Web 탐색
    ↓
후보 발견
    ↓
후보 조사 및 확장 탐색
    ↓
정규화
    ↓
중복 판정
    ↓
근거 검증
    ↓
품질 평가(Harness)
    ↓
Graph 상태 갱신
    ↓
저장 승인
    ↓
Google Spreadsheet 기록
    ↓
새로운 Seed 생성
    ↓
다음 Loop
```

핵심은 **한 번 검색하고 끝나는 수집기**가 아니라, 발견된 엔티티가 새로운 탐색의 출발점이 되는 **자율 탐색 Loop**다.

---

# 2. 범위

## 2.1 포함

- 코리아타운 및 한인 밀집지역 관련 데이터
- 한인 식당·마트·서비스업 등 사업체
- 한국 기업의 해외 법인·지사·사무소
- 한국계 브랜드의 해외 매장
- 한인회·기관·단체
- 공식적으로 확인 가능한 한국 관련 장소/조직
- 웹 검색 및 공개 데이터 조사
- 후보 발견, 검증, 중복 제거
- 관계 추출 및 내부 Graph 구성
- Google Spreadsheet 기록
- 반복적인 자율 탐색

## 2.2 제외

초기 버전에서는 다음을 만들지 않는다.

- GIS 프론트엔드
- 지도 UI
- 별도 PostGIS 서버
- Neo4j 필수 도입
- Qdrant
- Redis / Temporal
- Kubernetes
- 복잡한 분산 시스템
- 별도 데이터 포털

Graph는 **분석·탐색을 위한 내부 구조**로만 사용한다. 실제 표시 플랫폼은 기존 코리아타운DB다.

---

# 3. 설계 원칙

## 3.1 AI는 탐색하고, 코드가 저장을 통제한다

AI가 검색어·조사 순서·추가 탐색 여부를 판단할 수는 있지만, **AI의 출력이 그대로 Google Sheet에 기록되어서는 안 된다.**

```text
AI Agent
  ↓
Raw Candidate
  ↓
Deterministic Validation / Harness
  ↓
Approved Record
  ↓
Google Sheets Writer
```

## 3.2 Provenance 우선

모든 사실은 가능한 한 **출처와 수집 시점**을 함께 보존한다.

## 3.3 기존 데이터 존중

기존 Google Spreadsheet를 기준 데이터로 사용한다. 기존 행을 임의로 덮어쓰지 말고, 변경 근거를 남긴다.

## 3.4 무료 우선

가능한 경우 로컬 LLM 또는 무료 API, 무료 검색·크롤링 도구를 우선 사용한다. 다만 외부 API의 무료 한도와 약관은 별도 관리한다.

## 3.5 무한 탐색 금지

재귀 탐색에는 반드시 깊이·호출량·도메인·시간 등의 제한을 둔다.

---

# 4. 전체 아키텍처

```text
                     ┌──────────────────────┐
                     │ Existing Google Sheet│
                     │    Current DB        │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   State / Coverage   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │ Autonomous Loop      │
                     │ choose next action   │
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        Search Adapter    Places Adapter    Web Adapter
              └─────────────────┼─────────────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Candidate Extraction │
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Entity Resolution    │
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Graph Engineering    │
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Verification         │
                     │ + Provenance         │
                     └──────────┬───────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Harness              │
                     │ schema / privacy /   │
                     │ quality / confidence │
                     └──────────┬───────────┘
                                ▼
                   ┌────────────┴────────────┐
                   ▼                         ▼
             Approved                    Review Queue
                   │                         │
                   └────────────┬────────────┘
                                ▼
                     ┌──────────────────────┐
                     │ Google Sheets Writer │
                     └──────────┬───────────┘
                                ▼
                        New Seeds / State
                                │
                                └────→ Next Loop
```

---

# 5. Loop Engineering

## 5.1 목적

Loop Engineering은 에이전트가 **무엇을 다음에 조사할지 스스로 결정하고**, 조사 결과에 따라 다음 행동을 계속 선택하게 만드는 구조다.

기본 형태:

```text
State
  ↓
Choose Action
  ↓
Tool Call
  ↓
Observation
  ↓
Update State
  ↓
Evaluate Progress
  ↓
Next Action
```

## 5.2 Agent가 결정할 수 있는 행동

```text
SEARCH(query)
OPEN(url)
EXTRACT(entity)
VERIFY(entity)
EXPAND(entity)
CHECK_DUPLICATE(entity)
FOLLOW_RELATION(entity, relation)
PRIORITIZE(region/category)
WRITE(entity)
STOP(reason)
```

## 5.3 탐색 예시

```text
[Seed]
도쿄 + Korean restaurant
        ↓
[Candidate]
Restaurant A
        ↓
[Investigation]
공식 사이트 확인
        ↓
[Relation]
운영회사 B 발견
        ↓
[Expansion]
회사 B의 해외 지점 검색
        ↓
[Candidate]
오사카 / 후쿠오카 지점 발견
        ↓
[New Seeds]
회사 B + 일본 주요 도시
```

## 5.4 Loop 종료 조건

다음 중 하나면 현재 작업을 종료한다.

- 추가 후보가 거의 없음
- 동일 후보만 반복 발견
- 예산/호출량 한도 도달
- 최대 depth 도달
- 근거가 부족하여 더 이상 검증할 수 없음
- 목표 coverage 달성
- 동일 경로의 반복 탐색 감지

## 5.5 작업 우선순위

우선순위는 다음 요소를 조합한다.

```text
coverage gap
+ seed importance
+ expected discovery value
+ verification feasibility
- duplicate probability
- cost / request count
```

처음부터 복잡한 수학적 최적화가 필요하지 않다. 단순 점수 기반 priority queue로 시작한다.

---

# 6. Graph Engineering

## 6.1 목적

Graph Engineering은 수집한 데이터를 단순한 행(row)의 집합으로만 보지 않고 **엔티티와 관계의 연결 구조**로 관리하기 위한 것이다.

초기에는 별도 Graph DB를 사용하지 않고 **SQLite 또는 JSON 형태의 내부 Graph**로 충분하다.

## 6.2 Node

예:

```text
KOREATOWN
BUSINESS
COMPANY
BRANCH
ORGANIZATION
PERSON_PUBLIC
BRAND
CITY
COUNTRY
SOURCE
```

개인정보 수집 목적의 PERSON 노드는 기본적으로 사용하지 않는다.

## 6.3 Edge

예:

```text
LOCATED_IN
OPERATED_BY
OWNED_BY
BRANCH_OF
BELONGS_TO
RELATED_TO
HAS_SOURCE
LOCATED_NEAR
SAME_ENTITY_AS
```

## 6.4 예시

```text
Restaurant A
   │ OPERATED_BY
   ▼
Company B
   │ HEADQUARTERED_IN
   ▼
Seoul

Restaurant A
   │ LOCATED_IN
   ▼
Tokyo Koreatown

Company B
   │ HAS_BRANCH
   ▼
Osaka Branch
```

## 6.5 Graph의 역할

Graph는 다음에 사용한다.

- 새로운 탐색 Seed 생성
- 관계 기반 재탐색
- 중복/동일 엔티티 판단 보조
- 기업 본사 ↔ 지사 연결
- 브랜드 ↔ 매장 연결
- 지역 ↔ 사업체 연결
- 이미 조사한 경로 기억

Graph 자체를 사용자에게 보여주는 것이 목적이 아니다.

---

# 7. 데이터 모델

## 7.1 Canonical Entity

```ts
interface Entity {
  id: string;
  name: string;
  nameKo?: string;
  nameEn?: string;
  entityType: string;
  category?: string;

  country?: string;
  city?: string;
  address?: string;
  latitude?: number;
  longitude?: number;

  website?: string;
  phone?: string;
  placeId?: string;

  koreanRelevance?: string;
  parentEntityId?: string;

  verificationStatus:
    | 'CONFIRMED'
    | 'NEEDS_REVIEW'
    | 'UNVERIFIED'
    | 'REJECTED';

  confidenceScore?: number;
  provenance: Provenance[];
  discoveredAt: string;
  updatedAt: string;
}
```

## 7.2 Provenance

```ts
interface Provenance {
  sourceName: string;
  sourceUrl?: string;
  sourceType: string;
  collectedAt: string;
  verificationMethod?: string;
  evidence?: string;
}
```

## 7.3 Candidate

검증 전 데이터는 별도 Candidate로 관리한다.

```ts
interface Candidate {
  candidateId: string;
  rawName?: string;
  rawAddress?: string;
  discoveredFrom: string;
  sourceUrls: string[];
  extractedData: Record<string, unknown>;
  relatedEntityIds?: string[];
  status: 'NEW' | 'INVESTIGATING' | 'ACCEPTED' | 'REJECTED';
}
```

---

# 8. Discovery Layer

외부 데이터 소스는 Adapter로 분리한다.

```ts
interface DiscoveryAdapter {
  search(query: string, context?: SearchContext): Promise<DiscoveryResult[]>;
}
```

초기 Adapter:

```text
WebSearchAdapter
GooglePlacesAdapter
WebPageAdapter
OfficialSiteAdapter
```

향후 필요 시:

```text
CorporateRegistryAdapter
GovernmentDataAdapter
DirectoryAdapter
```

특정 공급자에 의존하지 않도록 Agent는 Adapter의 구현체를 직접 몰라야 한다.

## 8.1 현재 production discovery 정책

`MODE=production`에서는 CSE가 설정되지 않았다는 이유로 Mock 검색으로 fallback하지 않는다. 이 경우 검색 기능은 `SEARCH_UNAVAILABLE`로 기록하고, 활성화된 Google Places와 Places 결과의 공식 website 직접 조사만 수행한다. Mock adapter는 `MODE=mock`에서만 사용한다.

Places 결과에 website가 있으면 `WebPageAdapter`로 페이지를 연다. 페이지의 JSON-LD에 명시된 관계 필드(`parentOrganization`, `brand`, `manufacturer`, `department`, `subOrganization`)만 관련 Candidate로 확장하며, 추측으로 회사·브랜드·지점을 생성하지 않는다. 확장 Candidate에는 조사한 원본 페이지 URL을 source/provenance로 보존한다.

---

# 9. Candidate Extraction

검색 결과 자체를 바로 저장하지 않는다.

```text
Search Result
   ↓
Page / API Result
   ↓
LLM or Parser
   ↓
Candidate
```

추출 가능한 최소 정보:

- 이름
- 유형
- 카테고리
- 위치
- 웹사이트
- 전화
- 한국 관련성
- 출처
- 관계 정보

LLM은 **추출과 요약**에 사용하되, 사실을 새로 만들어내면 안 된다.

현재 2단계 구현의 결정적 웹 추출 경로는 공식 페이지의 JSON-LD parser다. 추출된 관계는 기존 Graph edge 타입으로 기록하고, 관련 Entity가 `CONFIRMED`이며 `NEW`일 때만 Sheet에 append한다.

---

# 10. Entity Resolution / 중복 제거

중복 판정 우선순위:

```text
1. placeId
2. 공식 website
3. 공식 전화번호
4. 정규화된 주소 + 이름
5. 좌표 + 이름
6. fuzzy name/address matching
7. Graph 관계 비교
```

결과:

```text
NEW
EXISTING
POSSIBLE_DUPLICATE
MERGE_REVIEW
```

자동 Merge는 높은 확신을 가진 경우에만 허용한다. 불확실하면 `MERGE_REVIEW`로 보낸다.

---

# 11. Verification

## 11.1 검증 원칙

**한 개의 약한 출처보다 독립적인 강한 출처를 우선한다.**

우선순위 예:

```text
공식 웹사이트
공식 기업/기관 자료
공공 등록정보
신뢰 가능한 지도/디렉터리
일반 웹페이지
검색 결과 snippet
```

## 11.2 검증 항목

- 실제 존재 여부
- 이름
- 주소
- 영업/운영 여부
- 공식 웹사이트
- 한국 관련성
- 기업/지사 관계
- 지역 관계

## 11.3 근거 부족

근거가 불충분하면 추정으로 확정하지 않는다.

```text
확인됨 → CONFIRMED
불충분 → NEEDS_REVIEW
잘못됨 → REJECTED
```

---

# 12. Harness Evaluation

Harness는 에이전트의 결과를 자동 검사하는 품질관리 계층이다.

```text
Candidate / Proposed Entity
          ↓
       Harness
          ├─ Schema
          ├─ Required fields
          ├─ Coordinate validity
          ├─ Duplicate check
          ├─ Privacy filter
          ├─ Provenance check
          ├─ Evidence quality
          └─ Confidence
          ↓
     Accepted / Review / Rejected
```

## 12.1 필수 검증

- 필수 필드 존재
- 타입 검사
- 좌표 범위 검사
- URL 형식 검사
- 개인정보 필터
- provenance 존재
- 중복 여부

## 12.2 Confidence Score

Confidence는 **보조지표**다. 사실을 보증하지 않는다.

간단한 초기 점수 예:

```text
공식 출처 확인                 +30
독립적인 추가 출처              +20
기업/기관 관계 공식 확인        +20
정확한 위치 확인                +15
한국 관련성 명확                +15
```

최대 100점.

권장 해석:

```text
80–100  강한 후보
60–79   중간 후보
0–59    추가 검토 필요
```

자동 `CONFIRMED` 여부는 점수만으로 결정하지 않는다.

---

# 13. Google Sheets Writer

Google Spreadsheet는 **최종 기록 대상**이다.

## 13.1 쓰기 원칙

```text
Validated Entity
     ↓
Schema Mapping
     ↓
Sheet Row
     ↓
Write
     ↓
Write Verification
```

## 13.2 중요한 규칙

- 검증 전 Candidate는 직접 기록하지 않는다.
- 기존 행을 임의로 덮어쓰지 않는다.
- 변경 시 변경 이유를 기록한다.
- 가능하면 안정적인 고유 ID를 사용한다.
- 실제 Sheet의 컬럼명을 먼저 확인한다.
- `CONFIRMED` 및 `NEW`인 Entity만 append한다.
- 기존 행은 삭제하거나 overwrite하지 않는다. 현재 자동 update는 안전을 위해 비활성화되어 있다.
- 완전히 빈 탭에서만 canonical header를 최초 1회 생성하며, 기존 데이터가 있는 탭의 행은 변경하지 않는다.

## 13.3 Adapter

```ts
interface SheetWriter {
  appendEntity(entity: Entity): Promise<void>;
  updateEntity(entity: Entity): Promise<void>;
  findExisting(key: string): Promise<Entity | null>;
}
```

---

# 14. 기존 DB와의 관계

```text
기존 코리아타운DB Google Sheet
           │
           ├── 현재 Entity
           ├── 현재 Koreatown
           └── 현재 Coverage
                    ↓
              Agent State
                    ↓
              새로운 수집
                    ↓
             검증 / 승인
                    ↓
          같은 Google Sheet에 기록
```

따라서 에이전트는 **기존 데이터를 읽고, 빈 곳을 찾아 수집하는 방식**으로 작동한다.

예:

```text
미국 데이터 많음
일본 데이터 중간
남미 데이터 부족
        ↓
Agent가 남미를 우선 탐색
```

---

# 15. Coverage Engineering

수집량 자체보다 **공간·유형별 누락을 줄이는 것**이 중요하다.

예시 상태:

```text
Country → City → Category → Count
```

Agent는 다음과 같은 공백을 찾는다.

```text
Seoul → Tokyo → Restaurant : 120
Seoul → Tokyo → Corporate : 3
Seoul → Osaka → Corporate : 0
```

이 경우 `Osaka + Korean Corporate`를 높은 우선순위 Seed로 생성할 수 있다.

초기에는 단순한 count 기반으로 구현한다.

---

# 16. Seed Engineering

Seed는 크게 4종류로 관리한다.

```text
REGION_SEED
ENTITY_SEED
RELATION_SEED
GAP_SEED
```

예:

```text
REGION_SEED
Tokyo + Korean Business

ENTITY_SEED
Samsung

RELATION_SEED
Samsung → overseas branches

GAP_SEED
Osaka + Korean corporate offices
```

발견된 엔티티와 관계가 새로운 Seed가 될 수 있다.

## 16.1 Seed priority와 재탐색 정책

확장으로 생성된 `ENTITY_SEED`와 `RELATION_SEED`는 SQLite에 저장되어 다음 iteration의 입력으로 다시 큐에 들어간다. `SeedQueue`는 priority가 높은 Seed를 먼저 실행한다.

```text
PENDING → RUNNING → DONE
                 ↘ FAILED (예산/실행 제한)
```

재탐색은 `MAX_DEPTH`, request/entity/runtime budget, query 방문 기록으로 제한한다. `--mode once`는 한 번의 bounded run만 수행하고, `--mode loop --iterations N`은 저장된 pending Seed를 다음 iteration에서 재사용한다. 따라서 Seed가 재귀적으로 생성되어도 무한 loop로 실행되지 않는다.

## 16.2 장시간 운영 스케줄러

운영용 장시간 실행은 `scripts/run_long_collection.sh`가 bounded loop 프로파일을 적용한다. 수동 1회 실행은 목표 하나를 오래 탐색하고, macOS daily scheduler는 `restaurant`, `market`, `company`, `association` 네 탐색 축을 순서대로 실행한다. daily scheduler는 매일 08:00에 각 축을 3 iterations, 최대 10분으로 실행하며 pending Seed를 이어서 처리한다. API key와 서비스 계정은 plist가 아니라 `.env`에서 로드하고, 최초 등록 전에는 `DRY_RUN=true`로 점검한다.

---

# 17. Agent State

에이전트는 현재까지의 탐색 상태를 기록한다.

```ts
interface AgentState {
  runId: string;
  currentGoal: string;
  visitedUrls: string[];
  visitedQueries: string[];
  processedCandidates: string[];
  discoveredEntityIds: string[];
  pendingSeeds: Seed[];
  depth: number;
  requestCount: number;
  startedAt: string;
  updatedAt: string;
}
```

중요한 상태는 프로그램 종료 후에도 복구할 수 있도록 저장한다.

초기에는 SQLite 하나면 충분하다.

---

# 18. 자동 실행 안전장치

반드시 제한한다.

```text
MAX_DEPTH
MAX_REQUESTS_PER_RUN
MAX_REQUESTS_PER_DOMAIN
MAX_NEW_ENTITIES_PER_RUN
MAX_RUNTIME
MAX_RETRIES
```

추가 안전장치:

- 동일 URL 반복 방문 방지
- 동일 query 반복 실행 방지
- 동일 entity 반복 조사 방지
- 실패한 도메인의 backoff
- robots.txt 및 서비스 약관 준수

---

# 19. 개인정보

기본 수집 대상은 조직·사업체 중심이다.

기본적으로 수집하지 않는다.

- 개인 휴대전화
- 개인 이메일
- 자택 주소
- 리뷰 작성자 정보
- 불필요한 개인 프로필

공식 사업체 전화·주소 등 공개된 사업 정보는 서비스 약관과 적용 법규를 확인한 뒤 사용한다.

---

# 20. 비용 전략

목표는 **가능한 한 $0에 가까운 운영**이다.

권장 우선순위:

```text
1. 기존 Google Sheets
2. 무료 웹 탐색 / 공개 데이터
3. 무료 LLM API 또는 로컬 LLM
4. 필요한 경우에만 유료 API
```

비용이 발생할 수 있는 영역:

- 검색 API
- Google Places 등 외부 API
- 대규모 LLM API 호출
- 프록시/크롤링 인프라

따라서 Agent는 호출량과 비용을 State에서 추적할 수 있어야 한다.

---

# 21. 권장 기술 스택

초기 구현:

```text
Python
SQLite
Google Sheets API
HTTP client
HTML parser
LLM Adapter
Search Adapter
```

LLM은 특정 공급자에 종속되지 않게 한다.

```ts
interface LLMProvider {
  generate(prompt: string): Promise<string>;
}
```

구현 예:

```text
OllamaProvider
GeminiProvider
OpenAIProvider
AnthropicProvider
```

실제 사용 가능한 Provider는 환경에 따라 선택한다.

---

# 22. 디렉터리 구조

```text
agent/
├── main.py
├── config.py
├── state/
│   └── store.py
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
├── adapters/
│   ├── sheets.py
│   ├── search.py
│   ├── places.py
│   ├── web.py
│   └── llm.py
├── models/
│   ├── entity.py
│   ├── candidate.py
│   └── seed.py
└── tests/
```

---

# 23. 구현 단계

## Phase 1 — 수집 기반

```text
[1] 기존 Google Sheet schema 분석
[2] Sheet Reader
[3] 내부 Entity 모델
[4] Normalizer
[5] 기본 Search Adapter
[6] Candidate 추출
[7] Sheet Writer
```

## Phase 2 — 품질관리

```text
[8] Entity Resolution
[9] Provenance
[10] Verification
[11] Harness
[12] Confidence Score
[13] Review Queue
```

## Phase 3 — 자율 Loop

```text
[14] Agent State
[15] Seed Queue
[16] Planner
[17] Loop Engine
[18] Coverage 기반 우선순위
[19] Recursive Discovery
```

## Phase 4 — Graph Engineering 강화

```text
[20] Node / Edge 모델
[21] 관계 추출
[22] Graph traversal
[23] Relation-based seed generation
[24] Graph 기반 duplicate 보조 판정
```

## Phase 5 — 확장

필요성이 실제로 입증될 때만 다음을 검토한다.

```text
PostgreSQL / PostGIS
Neo4j
Qdrant
Redis / Temporal
분산 Worker
```

---

# 24. 테스트 기준

## Unit Test

- 정규화
- 좌표 검증
- 중복 판정
- confidence 계산
- provenance 생성
- graph edge 생성
- seed 생성

## Integration Test

```text
Search
 → Candidate
 → Verify
 → Harness
 → Entity
 → Sheet Write
```

## Loop Test

가짜 검색 결과를 사용해 다음을 검증한다.

```text
Entity 발견
 → 관계 발견
 → 새 Seed 생성
 → 재탐색
 → 중복 방지
 → 종료 조건 작동
```

## Safety Test

- 잘못된 좌표
- 빈 이름
- 중복 결과
- 동일 URL 반복
- 근거 없는 AI 주장
- 개인정보 포함 결과
- API timeout
- Rate limit

---

# 25. 성공 기준

이 프로젝트의 성공은 **“지도가 만들어졌다”가 아니다.**

다음이 안정적으로 작동하면 핵심 목표를 달성한 것이다.

```text
기존 Sheet 읽기
      ↓
어디가 부족한지 판단
      ↓
스스로 검색
      ↓
새로운 후보 발견
      ↓
관련 정보를 추가 조사
      ↓
관계 연결
      ↓
중복 제거
      ↓
출처 검증
      ↓
Harness 통과
      ↓
Google Sheet 기록
      ↓
새로운 Seed 생성
      ↓
다음 탐색
```

즉 이 시스템의 본질은:

> **Google Spreadsheet를 최종 데이터 저장소로 사용하는 자율형 글로벌 한인 데이터 수집·검증 에이전트**다.
