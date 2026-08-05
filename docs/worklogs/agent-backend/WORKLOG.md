# Work Log

## Current status

- Current milestone: 공식 강남구 게시판 수집 adapter
- Working: health API, 승인 정책 fixture API, 공통 계약, 통합 공고·주민센터 새소식 수집과 상세 HTML 정규화
- In progress: 동일 문서의 PDF·HWPX·이미지 추출 결과 교차 검증
- Not implemented: HWPX/PDF 파서, DB, LangGraph 실행, Agent 실행 로그
- Blockers: 없음

## Next actions

- [x] 데모에 사용할 공식 게시판과 네 시나리오의 공고 후보를 확정한다.
- [x] 통합 공고와 주민센터 새소식의 본문·첨부파일 링크를 구조화한다.
- [ ] HTML과 동일 문서의 PDF·HWPX·이미지를 모두 파싱하고 결과를 교차 검증한다.
- [ ] 추출 결과를 EligibilityRule과 PolicyPackage 구조로 변환한다.
- [ ] 기존 FieldDefinition 재사용 또는 FieldDefinitionProposal 생성을 연결한다.
- [ ] AgentRun에 노드·도구 실행 로그와 review_required 사유를 기록한다.

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
