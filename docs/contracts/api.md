# API 계약

모든 API payload 키는 snake_case를 사용한다. 시민의 로컬 프로필과 판정 결과는 어떤 요청에도 포함하지 않는다.

## GET /health

응답은 status가 ok인 JSON 객체다.

## GET /api/policy-packages

승인된 review.status = approved 정책 패키지만 배열로 반환한다.

## GET /api/policy-packages/{policy_id}

승인된 정책 패키지 한 건을 반환한다. 존재하지 않거나 승인되지 않은 패키지는 404를 반환한다.

## POST /api/agent-runs

강남구 공식 공고 한 건의 Agent 실행을 생성한다. 시민 프로필이나 시민별 판정
결과는 요청에 포함하지 않는다.

요청:

```json
{
  "notice_url": "https://www.gangnam.go.kr/notice/view.do?...",
  "previous_policy_id": "demo-policy-v2"
}
```

- `notice_url`은 필수이며 허용된 강남구 공식 HTTPS host만 사용한다.
- `previous_policy_id`는 선택이다. 전달하면 DB의 승인된 PolicyPackage만 이전
  정책으로 사용하며 존재하지 않거나 미승인이면 404를 반환한다.

성공 응답은 HTTP 201이며 다음을 포함한다.

```json
{
  "agent_run": {},
  "policy_package": {},
  "field_definition_proposals": [],
  "field_definition_reviews": [],
  "evidence_issues": []
}
```

실행 중 수집·추출·검증이 실패해도 AgentRun이 생성됐다면 HTTP 201 응답의
`agent_run.status`를 `failed` 또는 `review_required`로 반환하고 DB에 기록한다.

## 관리자 최소 계약

- GET /api/field-definition-reviews
- POST /api/field-definition-reviews/{review_id}/approve
- POST /api/field-definition-reviews/{review_id}/reject
- GET /api/agent-runs/{run_id}

`GET /api/agent-runs/{run_id}`는 저장된 AgentRun 한 건을 반환하고, 존재하지 않으면
404를 반환한다.

HumanHandoff 별도 API는 만들지 않는다. 사람 검토 필요 상태는 AgentRun의 review_required, review_reason, unresolved_fields로 전달한다.
