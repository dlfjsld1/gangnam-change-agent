# Work Log

## Current status

- Current milestone: fixture 기반 관리자 검토 화면
- Working: Vite 앱, FieldDefinitionReview 목록·상세, evidence·canonical field 후보, 승인·수정·반려, AgentRun 로그, 수동 새 공고 확인 버튼, API 실패 fallback
- In progress: 실제 Backend 관리자 API 연결과 배포 환경 확인
- Not implemented: 승인된 정책의 시민 앱 통합 확인, 배포
- Blockers: 계약에 맞춘 관리자 API 구현 필요

## Next actions

- [x] fixture 기반 FieldDefinitionProposal 목록과 상세 검토 화면을 만든다.
- [x] 원문 evidence, 제안 필드, 기존 canonical field 후보를 함께 표시한다.
- [x] 승인·수정·반려 동작을 로컬 fixture 상태로 먼저 연결한다.
- [x] AgentRun의 review_required, review_reason, unresolved_fields와 실행 로그를 표시한다.
- [ ] 관리자 API 준비 후 fixture adapter를 실제 API adapter로 교체한다.
- [x] 새 공고 확인 버튼을 수동 크롤링 API에 연결하고 처리 결과를 새로고침한다.
- [ ] 승인된 PolicyPackage 공개 흐름과 시민 PWA 연결을 검증한다.
- [ ] 로컬 통합 확인 후 AWS에 관리자 웹·시민 PWA·백엔드를 배포한다.

## Completion criteria

- 관리자가 제안 필드의 근거를 보고 승인·수정·반려할 수 있다.
- AgentRun의 사람 검토 사유와 미해결 필드가 화면에 표시된다.
- 승인된 정책만 시민 API에 공개되는 흐름을 확인할 수 있다.
- API 미준비 또는 네트워크 실패 시 demo fixture fallback이 동작한다.
- 관리자 화면은 브라우저에서, 시민 화면은 설치 가능한 PWA로 동작한다.
- 관련 build와 로컬 end-to-end smoke check가 통과한다.

## Dependencies

- 첫 네 작업은 현재 계약과 fixture만으로 진행할 수 있다.
- 실제 승인·AgentRun 연동은 백엔드 관리자 API가 필요하다.
- AWS 배포는 로컬 end-to-end 흐름이 동작한 뒤 시작한다.

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition-proposal.schema.json

## Change history

### 2026-08-05 — 수동 새 공고 확인 버튼

#### Summary

관리자가 버튼을 누르면 `POST /api/notice-discovery-runs`로 강남구 공식 게시판 크롤링을 요청하고, 새 공고의 Agent 실행 결과와 검토 목록을 다시 표시하도록 연결했다. 실행 중 중복 요청을 막고 신규 공고 없음과 실패 상태를 안내한다.

#### Dependency

- Backend의 `Feat: 새 공고 수동 확인 API 추가` 변경이 main과 배포 환경에 반영되어야 한다.

#### Verification

- `frontend/admin`: `npm.cmd run build` passed

### 2026-08-04 — fixture 기반 관리자 검토 화면 구현

#### Summary

FieldDefinitionReview 목록·상세, evidence, canonical field 후보, 승인·수정·반려와 AgentRun 로그를 구현했다. 관리자 API가 없거나 네트워크가 실패하면 동일 DTO 형태의 demo fixture로 전환한다.

#### Verification

- `frontend/admin`: `npm.cmd run build` 통과

### 2026-08-04 — 다음 작업 큐 확정

#### Summary

fixture 기반 검토 화면부터 실제 API 통합과 AWS 배포까지의 순서와 완료 조건을 정리했다.

### 2026-08-04 — 초기 동기화 로그 생성

#### Summary

최신 동적 프로필 결정에 맞춰 관리자 검토 범위를 기록했다.
