# Decisions

## D-001 — 정책 기반 동적 프로필

- Date: 2026-08-04
- Status: accepted
- Previous design: age, residence, employment_status 같은 고정 프로필 필드
- New design: 정책 패키지의 required_profile_fields 객체 배열과 Record<string, ProfileValue> 로컬 프로필
- Reason: 새 정책 조건이 등장해도 앱 코드 변경 없이 필요한 질문을 추가하기 위함
- Affected areas: backend, frontend/citizen, frontend/admin
- Affected contracts: policy-package.schema.json, field-definition.schema.json, field-definition-proposal.schema.json

관리자 승인 전 새 필드는 시민 앱에 공개하지 않는다.

## D-002 — MVP 계약과 판정 범위 제한

- Date: 2026-08-04
- Status: accepted
- Decision: EligibilityRule 연산자를 equals, in, between, contains, exists와 AND/OR로 제한
- Match status: YES, NO, UNKNOWN, STALE
- Handoff: 별도 API 대신 AgentRun의 review_required, review_reason, unresolved_fields 사용
- Reason: 2일 MVP에서 세 담당 구현의 계약 불일치를 줄이기 위함
- Affected contracts: eligibility-rule.schema.json, match-status.schema.json, agent-run.schema.json

## D-003 — MVP 공식 수집 게시판

- Date: 2026-08-05
- Status: accepted
- Decision: 정책·혜택은 강남구청 통합 공고 시스템의 고시공고·채용공고를, 정류장 주변 정보는 주민센터 공통 새소식 게시판을 수집한다.
- Source identity: 통합 공고는 `not_ancmt_mgt_no`, 주민센터 새소식은 게시물 경로 ID를 사용한다.
- Demo notices: 청년 응시료 지원, 청년 행정인턴 최초·재공고, 청년 네트워크위원 모집, 삼성역 6104번 한시적 무정차
- Reason: 두 HTML 구조만으로 혜택, 정책 변경, 새로운 조건, 자주 이용하는 정류장 시나리오를 모두 재현할 수 있다.
- Affected areas: backend, frontend/citizen, frontend/admin
- Contract impact: 현재 PolicyPackage의 evidence와 impact_scope로 표현 가능하므로 공통 schema 변경 없음
