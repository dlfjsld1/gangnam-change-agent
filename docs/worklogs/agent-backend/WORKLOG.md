# Work Log

## Current status

- Current milestone: PostgreSQL 배포 통합 준비
- Working: health API, 실제 Agent 실행·조회 API, 공통 계약, 공식 게시판 수집, HTML·PDF·HWPX 추출, 최후 복구용 OpenAI 이미지 OCR adapter, 동일 문서 변형 교차 검증, 구조화 정책 후보와 PolicyPackage 조립, Field Registry 해석, Human Review 결과 생성, LangGraph 실행 흐름과 AgentRun 로그 누적, SQLite/PostgreSQL 공용 저장소 계층, 관리자 필드 검토 API, 정책 승인·반려와 승인 정책 Publish
- In progress: 관리자·통합 담당의 컨테이너와 PostgreSQL 연결 지원, 배포 전체 흐름 smoke 준비
- Not implemented: PostgreSQL live integration, 관리자 API 인증·접근 제한
- Blockers: none

## Next actions

- [x] 데모에 사용할 공식 게시판과 네 시나리오의 공고 후보를 확정한다.
- [x] 통합 공고와 주민센터 새소식의 본문·첨부파일 링크를 구조화한다.
- [x] HTML과 동일 문서의 PDF·HWPX를 파싱하고 동일 basename의 형식별 결과를 교차 검증한다.
- [x] 이미지와 스캔 PDF 페이지를 OpenAI Responses API OCR 흐름에 연결한다.
- [x] 공개 이미지·스캔 공고로 OpenAI OCR live smoke를 수행한다.
- [x] OCR 결과를 HTML·다른 첨부 근거와 대조해 의미가 달라진 오독을 검토 대상으로 전환한다.
- [x] 추출 결과를 EligibilityRule과 PolicyPackage 구조로 변환한다.
- [x] 기존 FieldDefinition 재사용 또는 FieldDefinitionProposal 생성을 연결한다.
- [x] 문서 추출·근거 비교 로그와 review_required 사유를 AgentRun에 기록한다.
- [x] LangGraph 전체 노드·도구 실행 로그를 AgentRun에 누적한다.
- [x] 같은 정책 계열의 이전 공고와 신규 공고를 비교해 구조화된 diff를 생성한다.
- [x] 실행·정책 후보·검토 상태를 저장소 인터페이스 뒤에 영속화한다.
- [x] LangGraph를 호출하고 결과를 반환하는 실제 Agent 실행 API를 추가한다.
- [x] FieldDefinitionReview 승인·수정·반려 API를 저장소와 연결한다.
- [x] 승인된 PolicyPackage만 시민 API에 공개하도록 Publish 흐름을 연결한다.
- [ ] 배포 PostgreSQL에서 Agent 실행·검토·Publish smoke를 수행한다.

## Completion criteria

- 실제 공고 1건이 출처와 함께 재현 가능하게 수집된다.
- 정보 부족 시 첨부파일 탐색 또는 사람 검토로 분기한다.
- 결과가 PolicyPackage와 AgentRun 스키마 검증을 통과한다.
- 모든 change와 조건에 evidence가 연결된다.
- 시민 프로필 데이터가 백엔드 입력·로그에 포함되지 않는다.
- 관련 `ruff`, `pytest`, schema validation이 통과한다.

## Dependencies

- 공식 소스와 데모 공고는 D-003으로 확정됐다.
- 공유 필드나 연산자 변경은 구현 전에 `docs/contracts/`에서 합의해야 한다.
- 관리자 API 연동 전까지 fixture 또는 저장소 인터페이스를 유지한다.

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition.schema.json
- docs/contracts/field-definition-proposal.schema.json

## Change history

### 2026-08-05 — 배포 Agent·검토·Publish smoke 준비

#### Summary

격리된 배포 DB를 대상으로 실제 Agent 실행, 생성된 FieldDefinitionReview 승인, PolicyPackage 승인과 시민 공개 조회를 순서대로 검증하는 재현 스크립트를 추가했다. 실수로 운영 데이터를 변경하지 않도록 `SMOKE_ALLOW_MUTATIONS=true`를 명시한 경우에만 실행된다.

#### Validation

- API 호출 순서와 이전 정책 ID 전달 unit test: passed
- PolicyPackage 미생성 시 중단 경로: passed
- PostgreSQL live smoke: 관리자·통합 담당의 컨테이너와 DB 준비 전이므로 미실행

### 2026-08-05 — 관리자 검토와 정책 Publish

#### Summary

FieldDefinitionReview 목록·승인·수정·반려 API와 PolicyPackage 승인·반려 API를 DB repository에 연결했다. 필드 승인 시 확정된 canonical key를 필수 프로필 필드, 재귀 EligibilityRule과 변경 항목에 반영한다. 연결된 모든 필드 검토가 승인된 정책만 Publish할 수 있으며 시민 조회 API는 승인된 DB 정책을 우선 제공하고 DB에 승인 정책이 없을 때만 데모 fixture를 사용한다.

#### Contract impact

`docs/contracts/api.md`에 additive 관리자 API와 상태 전이·Publish 조건을 명시했다. 기존 JSON Schema의 pending/approved/rejected 상태를 그대로 사용하며 시민 프로필 데이터는 입력·저장하지 않는다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 67 passed
- FieldDefinitionReview 승인·반려 JSON Schema validation: passed
- canonical field key 재작성과 재귀 EligibilityRule validation: passed
- 미승인·반려 field가 있는 PolicyPackage Publish 차단: passed
- 승인된 DB 정책 우선 공개와 fixture 차단 경로: passed

### 2026-08-05 — 실제 Agent 실행·조회 API

#### Summary

`POST /api/agent-runs`가 허용된 강남구 공고 URL과 선택적인 이전 승인 정책 ID를 받아 LangGraph를 실행한다. 실행 결과의 AgentRun, PolicyPackage 후보, FieldDefinitionProposal, FieldDefinitionReview를 DB에 저장하고 `GET /api/agent-runs/{run_id}`로 조회한다. FastAPI lifespan에서 DB schema를 초기화하며 POST CORS를 허용한다.

#### Contract impact

`docs/contracts/api.md`에 additive 실행·조회 API를 추가했다. 시민 프로필과 시민별 판정 결과는 요청·응답·DB에 포함하지 않는다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 60 passed
- 허용되지 않은 notice host 422, 미승인 이전 정책 404 경로 passed
- Agent 실행 결과와 Field Review repository 저장 경로 passed
- FastAPI lifespan SQLite schema 생성과 `/health` HTTP 200 smoke passed

### 2026-08-05 — SQLite/PostgreSQL 공용 저장소 계층

#### Summary

SQLAlchemy 모델과 AgentRepository를 추가해 공개 SourceNotice, AgentRun, PolicyPackage 후보, FieldDefinitionProposal과 검토 상태를 저장하도록 했다. 로컬은 SQLite, AWS 배포는 PostgreSQL을 사용하며 `DATABASE_URL`로 전환한다. 승인된 이전 PolicyPackage만 조회하는 repository 경로를 포함한다.

#### Contract impact

D-007에 팀 합의를 기록했으며 공통 JSON Schema는 변경하지 않았다. 시민 프로필과 시민별 판정 결과는 저장 대상에서 제외한다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 46 passed
- SQLite schema 생성·실행 결과 저장·제안 저장·승인 정책 조회 경로 passed
- PostgreSQL dialect table DDL compile: passed

### 2026-08-05 — 이전 정책 비교와 변경 diff 생성

#### Summary

명시적으로 선택된 이전 PolicyPackage와 신규 후보의 재귀 EligibilityRule, 시행일, 마감일, 필요한 행동을 비교해 `changes`를 생성한다. 이전 정책의 family와 version을 이어받고, 조건 확대·축소·추가·제거를 구분해 LangGraph의 검토 분기 전에 실행한다.

#### Contract impact

기존 PolicyPackage `changes` 구조를 그대로 사용하며 공통 schema는 변경하지 않았다. 이전 정책 계열 선택과 조회는 향후 저장소/API 단계의 책임으로 남긴다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 42 passed
- PolicyPackage JSON Schema validation: 조건 확대·날짜·행동 변경 경로 passed
- 재귀 AND/OR diff: 추가·제거·확대 경로 passed

### 2026-08-05 — LangGraph 실행 흐름 연결

#### Summary

공식 공고 수집, 문서 분석, 정책 후보 추출, PolicyPackage 조립을 `StateGraph`로 연결했다. 각 단계의 AgentNodeLog를 하나의 AgentRun에 누적하고, 검토 필요 결과는 Publish하지 않고 관리자 검토 대기로, 예외는 실패 상태로 분기한다.

#### Contract impact

공통 schema는 변경하지 않고 기존 AgentRun 계약을 그대로 사용한다. Field Registry와 Human Review의 세부 로직은 임시 위임 Task 범위로 남겨 두고 Graph topology만 연결했다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 38 passed
- AgentRun JSON Schema validation: completed·review_required·failed 경로 passed

### 2026-08-05 — TASK-001 Field Registry Node

#### Summary

정확한 key를 우선 적용하고, 공백·문장부호를 정규화한 label과 data type이 하나만 일치할 때 canonical FieldDefinition을 재사용하도록 FieldRegistry 해석 결과를 추가했다. 일치 후보가 없거나 여러 개면 pending FieldDefinitionProposal을 하나만 만들고, pending/rejected field는 새 제안 없이 unresolved field로 남긴다. 정책 조립은 해석된 canonical key를 eligibility rule에 사용한다.

#### Contract impact

공유 계약, LangGraph topology, `backend/app/agent/graph.py`, `backend/app/agent/state.py`는 수정하지 않았다. FieldDefinitionProposal과 PolicyPackage JSON Schema는 기존 검증을 통과했다.

#### Validation

- 대상 파일 `ruff check`: passed
- 대상 파일 `ruff format --check`: passed
- `pytest -q`: 41 passed, 5 warnings
- `pytest -q tests/test_field_registry.py tests/test_policy_builder.py`: 14 passed
- JSON Schema validation: FieldDefinitionProposal과 PolicyPackage validation passed
- 전체 `ruff check .`: 기존 범위 밖 파일의 21개 이슈로 failed
- 전체 `ruff format --check .`: 기존 `tests/test_document_extractor.py` 1개 파일로 failed

#### Dependency

- 작업 완료 후 Graph node 연결과 State partial update 연결은 Agent Backend 담당자가 진행한다.

### 2026-08-05 — TASK-002 Human Review 결과 생성

#### Summary

근거 불일치·추출 실패·미승인 field 사유를 최초 등장 순서로 중복 제거해 AgentRun에 기록하고, PolicyPackage review를 pending으로 유지하며 신규 FieldDefinitionProposal마다 pending FieldDefinitionReview를 생성하도록 Graph 독립 service를 연결했다.

#### Contract impact

기존 AgentRun, PolicyPackage, FieldDefinitionProposal, FieldDefinitionReview 계약을 그대로 사용했다. Graph·State·Publish API·DB·관리자 UI와 공통 schema는 변경하지 않았다.

#### Validation

- TASK-002 변경 파일 ruff check: passed
- TASK-002 변경 파일 ruff format --check: passed
- 전체 backend pytest: 36 passed, 5 warnings
- AgentRun, PolicyPackage, FieldDefinitionProposal, FieldDefinitionReview JSON Schema validation: passed
- repository 전체 ruff check: 기존 파일의 27개 위반으로 failed; TASK-002 변경 파일은 통과

#### Dependencies

- LangGraph 최종 node 등록과 ChangeAgentState mapping은 Agent Backend 담당 작업으로 남는다.
- pending review 저장과 관리자 API 연동은 Publish API·DB 구현 이후 연결한다.

### 2026-08-05 — FieldDefinition 재사용과 신규 제안 연결

#### Summary

정책 조건의 field key를 registry에서 조회해 `approved` 정의는 재사용하고, 없는 필드는 `pending` FieldDefinitionProposal로 반환하도록 연결했다. 이미 pending 또는 rejected 상태인 필드는 중복 제안하지 않고 `AgentRun.unresolved_fields`에 유지한다.

#### Contract impact

기존 FieldDefinitionProposal과 AgentRun 계약을 그대로 사용한다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 35 passed
- PolicyPackage와 FieldDefinitionProposal JSON Schema validation: passed

### 2026-08-05 — 구조화 정책 후보와 근거 검증

#### Summary

OpenAI Responses API의 Pydantic Structured Outputs로 공개 공고에서 `PolicyDraft`를 추출하고, 로컬 코드가 EligibilityRule·FieldDefinition·evidence를 현재 PolicyPackage 계약으로 조립하도록 구현했다. 원문에 없는 인용과 HTML 제목·이미지 OCR 불일치는 관리자 검토 사유로 전환한다.

#### Contract impact

공통 schema는 변경하지 않고 기존 PolicyPackage와 AgentRun 계약을 소비한다. 기본 모델은 `gpt-5.6-terra`이며 환경변수로 교체할 수 있다.

#### Validation

- ruff check: passed
- ruff format --check: passed
- pytest: 33 passed
- PolicyPackage JSON Schema와 재귀 EligibilityRule validation: passed
- live policy extraction: 공고 `61922`에서 조건 8개·행동 7개·PolicyPackage 후보 생성
- live evidence validation: 근거 문제 3개와 미승인 필드 8개를 감지해 review_required 전환

### 2026-08-05 — 공개 이미지 공고 OCR smoke

#### Summary

강남구 주민센터 공고 `1107105`의 공개 JPG 첨부를 Scrapling으로 수집하고 OpenAI OCR까지 실행하는 `backend/scripts/smoke_public_image_ocr.py`를 추가했다. 다운로드·형식 검증·OCR 호출은 성공했지만 제목의 `고유가`를 `교육가`로 오독하고도 현재 corpus가 검토 대상으로 전환하지 않는 사실을 확인했다.

#### Contract impact

공통 API schema 변경은 없다. 다음 단계에서 구조화된 조건과 근거 비교를 통해 의미가 달라진 OCR 오독을 `review_required`로 연결해야 한다.

#### Validation

- source ID: `1107105`
- attachment: `고유가 피해 지원금 사용가능 매장.jpg`
- extraction status: succeeded
- OCR text length: 32
- known mismatch: `고유가` → `교육가`
- current review_required: false

### 2026-08-05 — PDF 페이지 분류와 OpenAI OCR adapter

#### Summary

PDF의 각 페이지를 로컬 텍스트 또는 스캔 페이지로 분류하고, 스캔 페이지만 PNG로 렌더링해 OpenAI Responses API OCR에 보내도록 연결했다. 혼합 PDF는 페이지 순서와 처리 방법을 보존한다.

#### Contract impact

공통 API schema는 변경하지 않았고 D-005에 내부 처리 결정을 기록했다.

#### Tests

- ruff check: passed
- ruff format --check: passed
- pytest: 25 passed
- OpenAI 요청: fake client로 Responses API payload 검증
- Live OpenAI call: 합성 PNG의 `강남구 OCR 확인 2026` 문구가 원문과 정확히 일치해 인증·이미지 입력·응답 경로 통과

### 2026-08-05 — OpenAI OCR 실행 순서 제한

#### Summary

동일 문서 그룹의 로컬 PDF·HWPX 추출을 먼저 수행하고, 이미지와 스캔 PDF처럼 로컬 추출이 불가능한 부분에 OpenAI OCR을 실행하도록 순서를 변경했다. 필요한 OCR은 생략하지 않으며, 전체 추출과 비교 이후에도 미해결이면 관리자 검토로 전환한다.

#### Contract impact

공통 API schema 변경 없이 D-004와 D-005의 내부 실행 순서를 갱신했다.

#### Tests

- ruff check: passed
- ruff format --check: passed
- pytest: 27 passed

### 2026-08-05 — 문서 분석 AgentRun 연결

#### Summary

문서 추출과 형식별 근거 비교 결과를 기존 AgentRun 계약에 맞는 노드 로그, 실행 상태, 검토 여부와 사유로 변환했다.

#### Contract impact

기존 agent-run.schema.json을 그대로 사용했으며 공통 schema는 변경하지 않았다.

#### Tests

- ruff check: passed
- ruff format --check: passed
- pytest: 19 passed
- AgentRun JSON Schema validation: completed·review_required 경로 passed

### 2026-08-05 — 문서 변형 추출과 교차 검증

#### Summary

PDF와 HWPX 텍스트 추출기, Scrapling 첨부 다운로드, 동일 basename 그룹화, 전체 형식 실행, 대표 근거 선택과 충돌 검토 처리를 추가했다. 이미지 첨부는 OCR 공급자가 연결될 때까지 추출 실패와 검토 사유로 명시한다.

#### Contract impact

AgentRun의 기존 검토 필드로 표현할 수 있어 공통 schema는 변경하지 않았다.

#### Tests

- ruff check: passed
- ruff format --check: passed
- pytest: 17 passed
- live HWPX smoke: 공고 61922의 81,546 byte 첨부에서 5,701자 추출
- live PDF smoke: 개인정보 가능성이 없는 적절한 공식 fixture를 찾지 못해 생략

### 2026-08-05 — 공식 수집 소스와 parser 범위 확정

#### Summary

고시공고·채용공고와 주민센터 새소식으로 수집 범위를 제한하고 네 데모 시나리오의 공고를 확정했다. Scrapling 정적 Fetcher로 목록과 상세 페이지를 수집하고 본문·첨부파일 링크를 정규화했다.

#### Contract impact

기존 evidence와 impact_scope로 표현 가능해 공통 schema는 변경하지 않았다.

#### Tests

- ruff check: passed
- ruff format --check: passed
- pytest: 11 passed
- live Scrapling Fetcher smoke: 목록 3건·상세 2건 HTTP 200 및 구조화 성공

### 2026-08-04 — 다음 작업 큐 확정

#### Summary

실제 공고 수집부터 AgentRun 기록까지의 구현 순서와 완료 조건·의존성을 정리했다.

### 2026-08-04 — 동적 필드 보일러플레이트

#### Summary

새 조건의 FieldDefinitionProposal과 관리자 검토 필요 상태를 위한 최소 인터페이스를 추가했다.

#### Tests

- pytest: 7 passed
- ruff check: passed
