# TASK-002 — Human Review Node

> **Completed / Archived**
> 이 임시 위임 Task는 구현과 인계가 완료되었습니다. 현재 작업 지시로 사용하지 말고,
> 최신 상태와 다음 작업은 담당 Work log를 확인합니다.

## Task 성격

이 문서는 Admin·통합 담당의 Codex에게 Agent Backend의 Human Review 로직을
잠시 위임하기 위한 제한된 구현 Context다. 새 프로젝트를 시작하거나 Agent
Backend ownership을 이전하는 문서가 아니다.

## 구현 목적

Graph와 분리된 순수 로직으로 Publish 직전의 검토 필요 여부를 판단하고,
`AgentRun`, pending 정책 Review, pending field Review를 생성한다.

## 위임 이유

Agent Backend 담당이 Graph topology와 전체 실행 흐름을 계속 개발하는 동안
Admin 담당이 실제로 소비할 Human Review 출력과 예외 경로를 병렬로 검증하기
위함이다.

## 구현 범위

- 근거 불일치, 추출 실패, 미승인·모호 field를 검토 사유로 수집한다.
- 하나 이상의 사유가 있으면 `review_required=true`로 판단한다.
- 중복 사유를 제거해 `review_reason`에 안정적인 순서로 합친다.
- 미승인·모호 field key를 `unresolved_fields`에 중복 없이 기록한다.
- 현재 실행 결과를 나타내는 `AgentRun`을 생성한다.
- Publish 전 `PolicyPackage.review`를 `pending`으로 생성한다.
- 각 `FieldDefinitionProposal`에 대응하는 pending `FieldDefinitionReview`를
  생성한다.
- 필요한 단위 테스트와 JSON Schema validation을 추가한다.

## 수정하면 안 되는 영역

- LangGraph Graph와 topology
- `backend/app/agent/graph.py`
- `backend/app/agent/state.py`
- `docs/contracts/**`
- Publish API와 DB 저장
- `frontend/admin/**`와 관리자 UI
- 다른 담당 Work log

Graph 또는 State 변경이 필요해 보이면 구현하지 말고 Agent Backend Work log에
dependency로 기록한다.

## 입력 계약

- pending 상태의 `PolicyPackage` 후보
- `FieldDefinitionProposal` 목록
- evidence 검증 결과와 문서 추출 실패 사유
- 기존 review 상태와 기존 `unresolved_fields`
- `run_id`, `notice_id`, node 실행 로그
- 입력에는 시민 프로필이나 시민별 판정 결과를 포함하지 않는다.

## 출력 계약

Graph와 독립적인 내부 service/result로 다음 값을 반환한다.

- 현재 `docs/contracts/agent-run.schema.json`을 만족하는 `AgentRun`
- `review.status="pending"`, `reviewed_at=null`인 PolicyPackage 후보
- proposal마다 하나씩 생성한 pending `FieldDefinitionReview`

pending FieldDefinitionReview는 다음 의미를 유지한다.

- `review_id`: 실행과 field proposal을 식별하는 안정적인 ID
- `proposal`: 입력 proposal 원본
- `status`: `pending`
- `approved_field`: `null`
- `review_note`: `null`
- `reviewed_at`: `null`

Graph 연결을 위한 새 State field는 추가하지 않는다. 최종 node 등록과 State
mapping은 Agent Backend 담당이 한다.

## 관련 State

- `backend/app/agent/state.py`의 `ChangeAgentState`를 읽기만 한다.
- 기존 `review_required`, `review_reason`, `field_proposals`, `policy_package`
  의미를 유지한다.
- State 타입과 Graph node 등록은 수정하지 않는다.

## 관련 Schema

- `docs/contracts/agent-run.schema.json`
- `docs/contracts/field-definition-proposal.schema.json`
- `docs/contracts/field-definition-review.schema.json`
- `docs/contracts/policy-package.schema.json`의 `review`

Schema는 현재 계약 그대로 소비하고 수정하지 않는다.

## 완료 조건

- 검토 사유가 없는 경로의 AgentRun 상태가 계약과 일치한다.
- 근거 충돌과 추출 실패가 `review_required`와 `review_reason`에 반영된다.
- 신규·모호 field가 `unresolved_fields`와 pending review에 반영된다.
- 복합 사유와 field key가 중복 없이 안정적인 순서로 생성된다.
- PolicyPackage, AgentRun, FieldDefinitionReview가 실제 JSON Schema를 통과한다.
- 관련 `ruff`, formatter check, `pytest` 결과를 실제로 확인한다.
- 변경 파일과 검증 결과를 `docs/worklogs/agent-backend/WORKLOG.md`에 기록한다.
- Graph, State, Publish API와 관리자 UI가 변경되지 않았음을 확인한다.

## 완료 후 복귀

완료 결과를 Agent Backend 담당에게 전달한 뒤 Admin·통합 담당은
`feat/admin-integration`과 `docs/worklogs/admin-integration/WORKLOG.md`의 기존
Next actions로 복귀한다. 이 Task를 근거로 추가 Agent Backend 작업을 선택하지
않는다.
