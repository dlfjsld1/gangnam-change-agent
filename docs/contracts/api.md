# API 계약

모든 API payload 키는 snake_case를 사용한다. 시민의 로컬 프로필과 판정 결과는 어떤 요청에도 포함하지 않는다.

## GET /health

응답은 status가 ok인 JSON 객체다.

## GET /api/policy-packages

승인된 review.status = approved 정책 패키지만 배열로 반환한다.

## GET /api/policy-packages/{policy_id}

승인된 정책 패키지 한 건을 반환한다. 존재하지 않거나 승인되지 않은 패키지는 404를 반환한다.

## 관리자 최소 계약

- GET /api/field-definition-reviews
- POST /api/field-definition-reviews/{review_id}/approve
- POST /api/field-definition-reviews/{review_id}/reject
- GET /api/agent-runs/{run_id}

HumanHandoff 별도 API는 만들지 않는다. 사람 검토 필요 상태는 AgentRun의 review_required, review_reason, unresolved_fields로 전달한다.
