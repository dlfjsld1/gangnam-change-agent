# Work Log

## Current status

- Current milestone: 공식 강남구 게시판 수집 adapter
- Working: health API, 승인 정책 fixture API, 공통 계약, 공식 게시판 수집, HTML·PDF·HWPX 추출, 최후 복구용 OpenAI 이미지 OCR adapter, 동일 문서 변형 교차 검증
- In progress: 공개 스캔 공고 OCR smoke와 형식별 추출 결과의 정책 조건 비교
- Not implemented: DB, LangGraph 실행
- Blockers: 공개 스캔 공고 fixture 선정 필요

## Next actions

- [x] 데모에 사용할 공식 게시판과 네 시나리오의 공고 후보를 확정한다.
- [x] 통합 공고와 주민센터 새소식의 본문·첨부파일 링크를 구조화한다.
- [x] HTML과 동일 문서의 PDF·HWPX를 파싱하고 동일 basename의 형식별 결과를 교차 검증한다.
- [x] 이미지와 스캔 PDF 페이지를 OpenAI Responses API OCR 흐름에 연결한다.
- [ ] 공개 스캔 공고로 OpenAI OCR live smoke를 수행한다.
- [ ] 추출 결과를 EligibilityRule과 PolicyPackage 구조로 변환한다.
- [ ] 기존 FieldDefinition 재사용 또는 FieldDefinitionProposal 생성을 연결한다.
- [x] 문서 추출·근거 비교 로그와 review_required 사유를 AgentRun에 기록한다.
- [ ] LangGraph 전체 노드·도구 실행 로그를 AgentRun에 누적한다.

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
