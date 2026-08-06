# API 계약

모든 API payload 키는 snake_case를 사용한다. 시민의 로컬 프로필과 판정 결과는 어떤 요청에도 포함하지 않는다.

## GET /health

응답은 status가 ok인 JSON 객체다.

## GET /api/profile-fields

시민 PWA 온보딩에서 사용하는 승인된 canonical profile field 목록을
`display_order` 순서로 반환한다. 서버는 필드 정의만 제공하며 시민이 입력한 값은 이
API를 포함한 어떤 요청으로도 받지 않는다.

각 항목은 다음 메타 정보를 포함한다.

- `field_definition`: 승인된 FieldDefinition
- `onboarding_group`: 첫 설정의 기본 질문인 `core` 또는 선택 질문인 `optional`
- `eligibility_usable`: Agent가 자격 조건 canonical field로 재사용할 수 있는지
- `display_order`: PWA 표시 순서

기본 catalog는 `residence`, `age`, `employment_status`,
`frequent_bus_stops`, `interest_categories`다. `frequent_bus_stops`는 주변 영향
확인용이고 `interest_categories`는 추천·정렬용이므로 둘 다
`eligibility_usable=false`이며 정책의 `required_profile_fields`에 자동으로 넣지
않는다. `interest_categories`의 시민 답변은 IndexedDB에만 저장한다.

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
  "source_notice": {},
  "policy_package": {},
  "field_definition_proposals": [],
  "field_definition_reviews": [],
  "evidence_issues": []
}
```

`source_notice.attachments`는 원본 `url`과 선택적인 `storage_key`, `public_url`,
`sha256`을 포함한다. 아직 공개 archive되지 않은 첨부의 선택 필드는 null이다.

실행 중 수집·추출·검증이 실패해도 AgentRun이 생성됐다면 HTTP 201 응답의
`agent_run.status`를 `failed` 또는 `review_required`로 반환하고 DB에 기록한다.

## POST /api/notice-discovery-runs

관리자가 `새 공고 확인`을 요청할 때 강남구 공식 게시판 목록을 즉시 확인한다. 주기
스케줄러 계약은 아니다.

요청:

```json
{
  "max_new_notices": 1
}
```

- 기본값은 1, 최대값은 5다.
- 이미 DB에 저장된 원본 공고 URL은 Agent를 다시 실행하지 않는다.
- 새 공고는 최신 목록 순서로 제한 개수만 Agent 실행한다.
- 시민 프로필이나 시민별 판정 결과를 요청·저장하지 않는다.

응답:

```json
{
  "discovered_count": 12,
  "already_processed_count": 3,
  "processed_runs": []
}
```

게시판 목록 확인 자체가 실패하면 503을 반환한다. Agent 처리 결과가 failed 또는
review_required여도 생성된 AgentRun은 `processed_runs`에 포함한다.

## 관리자 최소 계약

- GET /api/agent-runs
- GET /api/field-definition-reviews
- GET /api/admin/agent-runs/{run_id}
- GET /api/admin/policy-packages
- GET /api/admin/policy-packages/{policy_id}
- POST /api/field-definition-reviews/{review_id}/approve
- POST /api/field-definition-reviews/{review_id}/reject
- POST /api/field-definition-reviews/{review_id}/edit (`approved_field`를 검증한 뒤 승인)
- GET /api/agent-runs/{run_id}
- POST /api/policy-packages/{policy_id}/approve
- POST /api/policy-packages/{policy_id}/reject

`GET /api/agent-runs/{run_id}`는 저장된 AgentRun 한 건을 반환하고, 존재하지 않으면
404를 반환한다.

### 관리자 조회

`GET /api/agent-runs`는 최신 실행부터 AgentRun 배열을 반환한다. 선택 query는 다음과
같다.

- `status`: AgentRun status 정확 일치
- `review_required`: 검토 필요 여부
- `limit`: 기본 50, 최대 100

`GET /api/field-definition-reviews`는 최신 검토부터 반환하며 `status`, `run_id`,
`limit`으로 필터링할 수 있다. `limit` 기본값은 100이고 최대 100이다.

`GET /api/admin/policy-packages`는 공개 여부와 관계없이 관리자 검토용 PolicyPackage를
최신 생성 순서로 반환한다. `review_status`, `run_id`, `limit`으로 필터링할 수 있다.
시민용 `GET /api/policy-packages`와 달리 pending/rejected package를 포함할 수 있다.

`GET /api/admin/policy-packages/{policy_id}`는 관리자용 package 한 건을 반환한다.
승인되지 않은 package도 조회하며 존재하지 않으면 404를 반환한다.

`GET /api/admin/agent-runs/{run_id}`는 관리자 상세 화면에 필요한 다음 실행 묶음을
반환하며 실행이 없으면 404를 반환한다.

```json
{
  "agent_run": {},
  "source_notice": {
    "attachments": [
      {
        "filename": "지원사업 안내.pdf",
        "url": "https://www.gangnam.go.kr/original.pdf",
        "storage_key": "review-attachments/gangnam_public_notice/61922/abc123-지원사업 안내.pdf",
        "review_url": "https://s3.ap-northeast-2.amazonaws.com/...signed...",
        "public_url": null,
        "sha256": "..."
      }
    ]
  },
  "policy_package": {},
  "field_definition_proposals": [],
  "field_definition_reviews": []
}
```

이 관리자 조회 API도 시민 프로필이나 시민별 판정 결과를 반환하지 않는다.
`review_url`은 S3 검토 저장소가 설정된 환경에서만 반환하는 단기 presigned URL이며
DB에 저장하지 않는다. 파싱 실패 여부와 관계없이 수집된 공식 첨부에 제공한다.

HumanHandoff 별도 API는 만들지 않는다. 사람 검토 필요 상태는 AgentRun의 review_required, review_reason, unresolved_fields로 전달한다.

### FieldDefinitionReview 승인

승인 요청은 관리자가 수정한 canonical field를 선택적으로 포함한다. 생략하면 제안된
필드를 승인한다.

`approved_field`에는 key와 label뿐 아니라 시민에게 표시할 `question`과 enum의
`allowed_values`도 수정해 전달할 수 있다. enum 선택지는 판정용 `value`와 시민용
`label`을 모두 포함해야 하며 빈 선택지를 승인하지 않는다.

```json
{
  "approved_field": null,
  "review_note": "공고 근거 확인"
}
```

승인된 field key가 제안 key와 다르면 같은 실행의 PolicyPackage
`required_profile_fields`와 재귀 EligibilityRule field를 함께 변경한다.

반려 요청은 선택적인 `review_note`만 포함한다. pending 검토만 승인 또는 반려할
수 있으며 완료된 검토를 반대 상태로 바꾸려 하면 409를 반환한다.

### PolicyPackage 승인과 공개

PolicyPackage 승인은 연결된 모든 FieldDefinitionReview가 approved일 때만 가능하다.
pending 또는 rejected 검토가 있으면 409를 반환한다. 승인된 package는
`review.status=approved`와 `reviewed_at`을 기록한 뒤 시민 정책 조회 API에 공개한다.

S3 첨부 archive가 설정된 배포 환경에서는 최종 승인 시 정책 evidence가 참조하는 공식
공개 첨부만 S3에 저장하고 evidence `source_url`을 고정 공개 URL로 변경한다. 개인정보
가능성이 있는 파일명은 409로 공개를 차단하고, 다운로드·S3 업로드 실패 시 정책을
승인하지 않고 503을 반환한다.

PolicyPackage 반려는 `review.status=rejected`를 기록하며 시민 정책 조회 API에
노출하지 않는다.
