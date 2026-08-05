# TASK-001 — Field Registry Node

## Task 성격

이 문서는 Citizen PWA 담당의 Codex에게 Agent Backend의 field registry 로직을
잠시 위임하기 위한 제한된 구현 Context다. 새 프로젝트를 시작하거나 Agent
Backend ownership을 이전하는 문서가 아니다.

## 구현 목적

LangGraph에 연결하기 전에 추출된 정책 조건을 기존 canonical
`FieldDefinition`과 매칭하고, 재사용할 수 없는 조건만
`FieldDefinitionProposal`로 만드는 로직을 독립적으로 구현·검증한다.

## 위임 이유

Agent Backend 담당이 Graph topology와 전체 실행 흐름을 계속 개발하는 동안
field registry의 결정론적 매칭과 제안 생성을 병렬로 완성하기 위함이다.

## 구현 범위

- 기존 `FieldRegistry`에서 canonical field를 검색한다.
- canonical `key` 정확 일치를 가장 먼저 적용한다.
- key가 일치하지 않으면 공백과 대소문자를 정규화한 `label`이 같고
  `data_type`도 같은 단일 field를 재사용한다.
- label·data_type 후보가 없거나 둘 이상으로 모호하면 기존 field를 임의로
  선택하지 않고 신규 `FieldDefinitionProposal`을 생성한다.
- 동일한 신규 field를 한 실행에서 중복 제안하지 않는다.
- registry에 이미 `pending` 또는 `rejected` field가 있으면 중복 proposal을
  만들지 않고 미해결 field로 유지한다.
- 필요한 단위 테스트와 JSON Schema validation을 추가한다.

## 수정하면 안 되는 영역

- LangGraph Graph와 topology
- `backend/app/agent/graph.py`
- `backend/app/agent/state.py`
- `docs/contracts/**`
- `frontend/citizen/**`
- Citizen PWA matcher, IndexedDB, 질문 UI
- 다른 담당 Work log

Graph 또는 State 변경이 필요해 보이면 구현하지 말고 Agent Backend Work log에
dependency로 기록한다.

## 입력 계약

- 추출된 정책 조건과 후보 `FieldDefinition`
- 현재 canonical `FieldRegistry`
- 현재 `ChangeAgentState`의 기존 field 관련 값
- 입력에는 시민 프로필이나 시민별 판정 결과를 포함하지 않는다.

## 출력 계약

내부 service/result로 다음 값을 반환한다.

- `resolved_fields: list[FieldDefinition]`
- `field_proposals: list[FieldDefinitionProposal]`
- `unresolved_fields: list[str]`
- `review_required: bool`
- `review_reason: str | None`

Graph 연결을 위한 새 State field는 추가하지 않는다. 기존 State에 반영 가능한
값만 partial update로 제공하고, 최종 State mapping은 Agent Backend 담당이 한다.

## 관련 State

- `backend/app/agent/state.py`의 `ChangeAgentState`를 읽기만 한다.
- 기존 `extracted_conditions`, `field_proposals`, `review_required`,
  `review_reason` 의미를 유지한다.
- State 타입과 Graph node 등록은 수정하지 않는다.

## 관련 Schema

- `docs/contracts/field-definition.schema.json`
- `docs/contracts/field-definition-proposal.schema.json`
- `docs/contracts/policy-package.schema.json`의 `required_profile_fields`

Schema는 현재 계약 그대로 소비하고 수정하지 않는다.

## 완료 조건

- key 정확 일치 field가 재사용된다.
- 정규화 label과 동일 data type의 단일 field가 재사용된다.
- 후보 없음과 복수 후보가 신규 proposal 또는 미해결 상태로 처리된다.
- pending/rejected field와 한 실행 내 동일 field가 중복 제안되지 않는다.
- 생성한 proposal이 실제 FieldDefinitionProposal JSON Schema를 통과한다.
- 관련 `ruff`, formatter check, `pytest` 결과를 실제로 확인한다.
- 변경 파일과 검증 결과를 `docs/worklogs/agent-backend/WORKLOG.md`에 기록한다.
- Graph와 State가 변경되지 않았음을 확인한다.

## 완료 후 복귀

완료 결과를 Agent Backend 담당에게 전달한 뒤 Citizen PWA 담당은
`feat/citizen-pwa`와 `docs/worklogs/citizen-pwa/WORKLOG.md`의 기존 Next actions로
복귀한다. 이 Task를 근거로 추가 Agent Backend 작업을 선택하지 않는다.
