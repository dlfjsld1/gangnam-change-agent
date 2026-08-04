# Work Log

## Current status

- Current milestone: fixture 기반 Backend 보일러플레이트
- Working: health API, 승인 정책 fixture API, FieldDefinition·EligibilityRule·PolicyPackage·AgentRun 계약
- In progress: 계약 기반 Pydantic 모델 정렬
- Not implemented: Scrapling, HWPX/PDF 파서, DB, Agent 실행 로그
- Blockers: 실제 강남구 공고와 첨부파일 후보 확정 필요

## Next actions

- [ ] 데모에 사용할 강남구 공고 상세 페이지와 이전 공고 후보를 각 1건 확정한다.
- [ ] 공고 상세 HTML을 수집하고 본문·첨부파일 링크를 구조화한다.
- [ ] 본문 정보가 부족할 때 PDF/HWPX 도구를 선택하는 Agent 분기를 추가한다.
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

- 첫 작업에는 팀이 합의한 실제 공고 URL과 비교 대상이 필요하다.
- 공유 필드나 연산자 변경은 구현 전에 `docs/contracts/`에서 합의해야 한다.
- 관리자 API 연동 전까지 fixture 또는 저장소 인터페이스를 유지한다.

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition.schema.json
- docs/contracts/field-definition-proposal.schema.json

## Change history

### 2026-08-04 — 다음 작업 큐 확정

#### Summary

실제 공고 수집부터 AgentRun 기록까지의 구현 순서와 완료 조건·의존성을 정리했다.

### 2026-08-04 — 동적 필드 보일러플레이트

#### Summary

새 조건의 FieldDefinitionProposal과 관리자 검토 필요 상태를 위한 최소 인터페이스를 추가했다.

#### Tests

- pytest: 7 passed
- ruff check: passed
