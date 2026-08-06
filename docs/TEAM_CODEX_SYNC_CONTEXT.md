# Team Codex Sync Context — 기획 변경 공유 체계

## 이 문서의 목적

이 문서는 팀원마다 별도의 Codex 세션을 사용하더라도 프로젝트의
기획 변경, 공통 계약, 담당별 구현 상태를 같은 기준으로 유지하기 위한
협업 문맥이다.

이 문서는 저장소 루트의 `AGENTS.md`와 함께 Codex에 제공한다.

핵심 원칙:

> 팀원 개인의 Codex 대화는 서로 공유되지 않는다.
> 최신 기획과 변경사항은 Git 저장소 안의 문서와 계약으로 전달한다.

---

# 1. 현재 프로젝트 역할 분배

아래 표가 기본 역할 분배다.

| 사람 | 맡는 범위 | 최종 결과물 |
|---|---|---|
| **Agent·백엔드 담당** | 크롤링, HTML/HWPX 분석, LangGraph, 이전 공고 비교, 근거 검증, 동적 조건 제안, 정책 JSON 생성 | `공고 → 정책 패키지 API` |
| **시민용 프론트 담당** | PWA, 동적 로컬 프로필, IndexedDB, `YES/NO/UNKNOWN/STALE`, 추가 질문, 사용자 A/B 화면 | `정책 JSON → 시민별 결과 화면` |
| **관리자·통합·배포 담당** | 관리자 검토 화면, 동적 필드 승인/반려, Agent 로그, 프론트·백 통합, AWS 배포, 데모 안정화 | `Agent 결과 → 승인 → 배포된 서비스` |

Agent 개발 일부를 다른 팀원에게 나누는 것은 선택사항이다.

- 선택적 보조 참여가 기본 소유권을 바꾸지는 않는다.
- 같은 파일을 두 사람이 동시에 수정하지 않는다.
- 선택 분배를 적용할 때 담당 파일과 반환 계약을 먼저 확정한다.
- 기본적으로 Agent·백엔드 담당이 전체
  `공고 → 정책 패키지 API` 흐름을 책임진다.

## 임시 위임 Task

`docs/tasks/`의 Task 문서는 다른 담당의 Codex 세션에 Agent Backend 구현
일부를 잠시 맡기기 위한 제한된 문맥이다. 새 프로젝트를 시작하거나 코드
ownership을 이전하는 문서가 아니다.

Task 수행자는 다음 순서만 읽고 구현을 시작한다.

1. `AGENTS.md`
2. 배정받은 `docs/tasks/TASK-*.md`
3. Task에 명시된 `docs/contracts/` 파일
4. `docs/worklogs/agent-backend/WORKLOG.md`

운영 규칙:

- Task에 적힌 범위와 수정 금지 영역을 우선한다.
- Graph topology와 State 변경은 Agent Backend 담당에게 남긴다.
- backend 구현 결과와 실제 검증은 Agent Backend Work log에 기록한다.
- Task 완료는 장기 ownership 변경이나 Agent Backend 다음 작업의 인수를 뜻하지 않는다.
- 완료 후 Citizen 또는 Admin 담당은 자기 feature 브랜치의 원래 Work log와 Next actions로 즉시 복귀한다.
- 같은 backend 파일을 Agent Backend 담당과 동시에 수정하지 않도록 시작 전에 작업 파일을 합의한다.

---

# 2. 왜 저장소 문서가 필요한가

팀원 A의 Codex에게 기획을 설명해도 팀원 B의 Codex는 그 내용을 알지 못한다.

따라서 다음 방식은 사용하지 않는다.

```text
팀 채팅에만 기획 변경 설명
→ 각 팀원이 자기 Codex에 다르게 요약
→ 서로 다른 schema와 동작 구현
```

대신 다음 흐름을 사용한다.

```text
기획 변경 확정
→ 저장소 공통 문서 수정
→ 공통 계약 수정
→ 문서 커밋
→ 팀원 pull
→ 각 Codex가 최신 문서와 자기 코드 비교
→ 담당 코드 수정
→ 담당 work log 갱신
```

---

# 3. 중앙 집중 문서 구조

문서가 코드 폴더마다 흩어지지 않도록 모든 프로젝트 문서를
`docs/` 아래에 모은다.

```text
.
├─ AGENTS.md
└─ docs/
   ├─ PROJECT_CONTEXT.md
   ├─ DECISIONS.md
   ├─ tasks/
   │  ├─ TASK-001-field-registry-node.md
   │  └─ TASK-002-review-node.md
   ├─ contracts/
   │  ├─ policy-package.schema.json
   │  ├─ field-definition.schema.json
   │  ├─ profile-field-catalog-item.schema.json
   │  └─ api.md
   ├─ deployment/
   │  └─ BACKEND_CONTAINER_HANDOFF.md
   └─ worklogs/
      ├─ agent-backend/
      │  └─ WORKLOG.md
      ├─ citizen-pwa/
      │  └─ WORKLOG.md
      └─ admin-integration/
         └─ WORKLOG.md
```

루트에는 공통 실행 규칙인 `AGENTS.md`만 둔다.

소스 폴더 안에는 별도의 `WORKLOG.md`를 만들지 않는다.

---

# 4. 문서별 역할

## `docs/PROJECT_CONTEXT.md`

현재 유효한 제품 기획을 기록한다.

- 지금 서비스가 무엇인지
- 현재 확정된 역할 분배
- 현재 Agent 흐름
- 현재 개인정보 처리 방식
- 현재 MVP 범위
- 현재 사용자 경험

과거 설계를 계속 쌓는 파일이 아니다.

기획이 바뀌면 이전 설명을 그대로 남기는 것이 아니라,
현재 설계가 명확하게 보이도록 갱신한다.

## `docs/DECISIONS.md`

프로젝트 전체에 영향을 주는 결정과 이유를 날짜별로 남긴다.

예:

- 고정 프로필에서 동적 프로필로 변경
- Vector DB를 사용하지 않기로 결정
- HWPX 실패 시 human handoff
- 관리자 승인 전 정책 패키지 비공개

기록 항목:

```text
결정 ID
날짜
상태
이전 설계
새 설계
결정 이유
영향받는 담당 영역
영향받는 계약
```

## `docs/contracts/`

백엔드, 시민 PWA, 관리자 화면이 함께 따라야 하는 실제 계약이다.

예:

- 정책 패키지 JSON
- 동적 필드 정의
- eligibility rule
- Agent 실행 로그
- human handoff
- API 요청·응답
- 공개 근거 첨부의 관리자·PWA 통합

공통 JSON이나 API가 바뀌면 구현보다 계약 문서를 먼저 수정한다.

공개 근거 첨부를 화면에 연결하는 Citizen/Admin 담당 Codex는 다음을 추가로 읽는다.

1. `docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md`
2. `docs/contracts/api.md`
3. 자신의 담당 Work log

## `docs/worklogs/`

담당별 현재 구현 상태와 변경 이력을 기록한다.

Work log는 프로젝트 전체 기획을 공지하는 파일이 아니다.

- `PROJECT_CONTEXT.md`: 현재 기획
- `DECISIONS.md`: 공통 결정과 이유
- `contracts/`: 공유되는 코드 계약
- `WORKLOG.md`: 각 담당의 실제 구현 상태

## `docs/tasks/`

다른 담당의 Codex가 Agent Backend의 제한된 구현을 잠시 수행할 때 필요한
목적, 범위, 입력·출력 계약, 금지 영역과 복귀 절차를 기록한다.

- Task 문서는 현재 코드와 contracts를 대체하지 않는다.
- Task에 명시되지 않은 Agent Backend 작업으로 범위를 확장하지 않는다.
- Task 종료 후 장기 진행 상태는 담당별 Work log에서만 관리한다.

## `docs/deployment/`

담당 간 배포 경계, 실행 환경변수, build context, health check와 현재 준비 상태를
기록한다. 백엔드 Dockerfile 또는 AWS 실행 환경을 다루는 관리자·통합 담당과
그 Codex는 다음 순서로 읽는다.

1. `AGENTS.md`
2. `docs/deployment/BACKEND_CONTAINER_HANDOFF.md`
3. `docs/DECISIONS.md`의 데이터베이스·보안 결정
4. `docs/contracts/api.md`
5. `docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md`
6. `docs/worklogs/admin-integration/WORKLOG.md`

### 현재 백엔드 배포 인계

관리자·통합 담당 Codex는 Docker/PostgreSQL 작업을 시작할 때 다음 현재 상태를 기준으로
삼는다.

- Agent 실행, FieldDefinitionReview 승인·수정·반려, PolicyPackage 승인·반려와
  승인 정책 공개 API는 백엔드에 구현되어 있다.
- `backend/scripts/smoke_agent_review_publish.py`로
  `Agent 실행 → 필드 검토 승인 → 정책 승인 → 시민 API 공개`를 검증한다.
- smoke는 실제 DB 데이터를 생성·승인하므로 격리된 로컬 또는 배포 검증 DB에서만
  `SMOKE_ALLOW_MUTATIONS=true`로 실행한다.
- `BACKEND_BASE_URL`, `SMOKE_NOTICE_URL`을 설정하고, 이전 정책 diff가 필요할 때만
  `SMOKE_PREVIOUS_POLICY_ID`를 설정한다.
- PostgreSQL 연결, Docker build/run과 실제 smoke 결과는
  `docs/worklogs/admin-integration/WORKLOG.md`에 기록한다.
- 실패 원인이 백엔드 API나 repository이면 Agent·백엔드 담당에게 전달하고, Agent
  topology나 parser를 배포 작업에서 임의로 수정하지 않는다.
- 공개 첨부 프론트 연결은
  `docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md`의 관리자·PWA 절차를
  따른다.

---

# 5. 코드와 Work log 매핑

| 코드 영역 | 읽고 갱신할 로그 |
|---|---|
| `backend/**` | `docs/worklogs/agent-backend/WORKLOG.md` |
| `frontend/citizen/**` | `docs/worklogs/citizen-pwa/WORKLOG.md` |
| `frontend/admin/**` | `docs/worklogs/admin-integration/WORKLOG.md` |
| `infra/**` | `docs/worklogs/admin-integration/WORKLOG.md` |

공통 계약을 바꾼 사람은 다른 담당자의 Work log를 임의로 수정하지 않는다.

대신:

1. `DECISIONS.md`에 영향받는 담당 영역을 기록한다.
2. `contracts/`를 수정한다.
3. 각 담당자가 pull한 뒤 자신의 구현과 Work log를 갱신한다.

---

# 6. Work log 형식

각 Work log는 같은 형식을 사용한다.

```markdown
# Work Log

## Current status

- Current milestone:
- Working:
- In progress:
- Not implemented:
- Blockers:

## Next actions

- [ ] 우선순위가 가장 높은 미완료 작업

## Completion criteria

- 검증 가능한 완료 조건

## Dependencies

- 선행 작업, 다른 담당 계약, 외부 입력

## Current contracts

- `docs/contracts/...`

---

## Change history

### YYYY-MM-DD — Change title

#### Summary

#### Changed files

#### Contract impact

#### Tests

#### Remaining work

#### Blockers
```

운영 규칙:

- `Current status`는 항상 현재 저장소 상태로 갱신한다.
- `Change history`는 날짜별로 아래에 추가한다.
- 의미 있는 구현 변경만 기록한다.
- 실제로 실행한 테스트와 실제 결과를 적는다.
- API, schema, DB, 동작 영향이 있으면 반드시 적는다.
- 포맷팅, 오타, 주석만 바꾼 작업은 기록하지 않는다.

---

# 7. 기획 변경 전달 절차

## 프로젝트 전체에 영향을 주는 변경

예:

- 정책 패키지 구조 변경
- 새로운 Agent 분기
- 개인정보 저장 방식 변경
- 새 동적 조건 타입
- 관리자 승인 절차 변경

절차:

```text
1. PROJECT_CONTEXT 갱신
2. DECISIONS에 변경 이유 기록
3. contracts 수정
4. 문서/계약 커밋
5. 팀원 pull
6. 각 팀원의 Codex가 충돌 분석
7. 담당 코드 수정
8. 담당 Work log 갱신
9. 테스트 후 코드 커밋
```

문서 커밋 예:

```text
Docs: 동적 프로필 설계와 공통 계약 반영
```

## 담당 내부 구현만 바뀌는 경우

예:

- Scrapling selector 수정
- 시민 카드 UI 내부 구조 변경
- AWS health check 수정

이 경우:

- 프로젝트 기획이 바뀌지 않았다면 `PROJECT_CONTEXT.md`는 수정하지 않는다.
- 공통 설계 결정이 아니라면 `DECISIONS.md`도 수정하지 않는다.
- 담당 Work log와 필요한 테스트만 갱신한다.
- 공통 계약에 영향이 있으면 `contracts/`까지 수정한다.

---

# 8. 최신 공통 결정 예시 — 정책 기반 동적 프로필

현재 프로젝트의 중요한 차별점이다.

## 이전 설계

시민 프로필을 다음처럼 고정된 속성으로만 설계했다.

```text
나이
거주지
고용 상태
```

이 구조는 새 정책에서 `군필자`, `창업 3년 이내`,
`주 30시간 미만 근무` 같은 조건이 나오면 대응하기 어렵다.

## 최신 설계

```text
Agent가 정책 조건 추출
→ 기존 canonical field registry 검색
→ 같은 개념이 있으면 재사용
→ 없으면 FieldDefinition 제안
→ 의미가 모호하면 관리자 검토
→ 승인된 필드만 정책 패키지로 배포
→ PWA의 로컬 프로필에 값이 없으면 UNKNOWN
→ 승인된 질문을 사용자에게 한 개 제시
→ 답변을 IndexedDB에만 저장
→ 즉시 결정론적으로 재판정
```

발표용 핵심 문장:

> 정책이 바뀌면 앱 코드가 아니라 사용자에게 필요한 질문이 함께 바뀝니다.

## 영향받는 담당

### Agent·백엔드

- 정책 조건 추출
- 기존 field registry 조회
- 새로운 `FieldDefinitionProposal` 생성
- 원문 evidence 연결
- 관리자 handoff
- 승인된 필드를 포함한 정책 패키지 생성

### 시민용 PWA

- 고정 프로필 interface 사용 금지
- `Record<string, ProfileValue>` 형태의 동적 로컬 프로필
- `required_profile_fields` 기반 질문 UI
- `UNKNOWN → 질문 → 저장 → 재판정`
- 답변은 IndexedDB에만 저장
- 서버로 시민 프로필이나 판정 결과를 보내지 않음
- 승인 정책 evidence의 S3·CloudFront 또는 공식 원문 URL 표시
- 첨부 접근 실패와 로컬 정책 판정 흐름 분리

### 관리자·통합

- 새 필드 제안 표시
- 원문 근거 표시
- canonical key 중복 후보 표시
- 질문·허용값 수정
- 승인·반려
- 승인된 필드만 시민 API에 공개
- 실행 상세의 원본 공고·첨부 표시
- 정책 최종 승인 후 S3 공개 URL 갱신과 409/503 처리

## 공통 계약 변경

`required_profile_fields`는 다음이 아니다.

```json
["age", "residence", "employment_status"]
```

객체 배열이어야 한다.

```json
[
  {
    "key": "military_service_status",
    "label": "병역 이행 상태",
    "data_type": "enum",
    "allowed_values": [
      {
        "value": "completed",
        "label": "이행함"
      },
      {
        "value": "not_completed",
        "label": "미이행"
      },
      {
        "value": "exempted",
        "label": "면제"
      }
    ],
    "question": "병역 의무를 이행하셨나요?",
    "sensitivity": "medium",
    "review_status": "approved"
  }
]
```

`군필자`의 정확한 포함 범위가 불명확하면 자동 승인하지 않는다.

---

# 9. 팀원 Codex가 문서 변경을 받은 뒤 할 일

각 팀원은 최신 커밋을 pull한 뒤 자기 Codex에 다음과 같이 지시한다.

```text
저장소의 최신 문서를 먼저 읽어라.

읽을 순서:
1. 루트 AGENTS.md
2. docs/PROJECT_CONTEXT.md
3. docs/DECISIONS.md
4. 현재 작업과 관련된 docs/contracts/*
5. 내 담당 영역의 docs/worklogs/*/WORKLOG.md

최근 확정된 기획 변경을 요약하고,
내 담당 구현과 충돌하는 부분을 파일 단위로 찾아라.

아직 코드를 수정하지 말고 다음을 보고해라.

1. 새로 확정된 사항
2. 기존 구현과 충돌하는 부분
3. 변경해야 할 schema와 API
4. 내 담당 범위에서 수정할 파일
5. 다른 담당자와 먼저 합의할 부분
6. 필요한 테스트
```

분석을 확인한 뒤 두 번째 지시:

```text
확인한 변경사항 중 내 담당 범위만 수정해라.

- 공통 계약을 임의로 다시 바꾸지 마라.
- 다른 담당 폴더를 수정하지 마라.
- 관련 테스트를 실제로 실행해라.
- 작업이 끝나면 내 담당 Work log를 갱신해라.
- 수정 파일, 테스트 결과, 남은 문제를 보고해라.
- Git push는 하지 마라.
```

---

# 10. 최초 저장소 설정 시 Codex가 할 일

이 문서와 `AGENTS.md`를 받은 초기 Codex는 다음을 수행한다.

1. 기존 저장소 구조를 먼저 조사한다.
2. 루트에 제공된 `AGENTS.md`를 배치하거나 기존 파일과 병합한다.
3. 다음 구조를 생성한다.

```text
docs/
├─ PROJECT_CONTEXT.md
├─ DECISIONS.md
├─ contracts/
└─ worklogs/
   ├─ agent-backend/WORKLOG.md
   ├─ citizen-pwa/WORKLOG.md
   └─ admin-integration/WORKLOG.md
```

4. 기존 최신 기획 문서가 있다면 `PROJECT_CONTEXT.md`로 정리한다.
5. 동적 프로필 결정을 `DECISIONS.md`의 첫 accepted decision으로 기록한다.
6. 세 Work log에 현재 보일러플레이트 상태를 기록한다.
7. 기존 API/schema와 동적 프로필 설계의 충돌을 보고한다.
8. 아직 기능 코드를 대규모로 수정하지 않는다.
9. 생성·수정한 문서 목록을 보고한다.
10. Git push는 하지 않는다.

---

# 11. Codex 완료 보고 형식

```text
1. 확인한 기존 문서와 코드 구조
2. 생성하거나 이동한 문서
3. AGENTS.md 반영 내용
4. PROJECT_CONTEXT 현재 상태
5. DECISIONS에 기록한 결정
6. 생성한 contracts 또는 필요한 contracts
7. 담당별 Work log 초기 상태
8. 현재 구현과 최신 기획의 충돌
9. 다음 구현 순서
10. Git 초기 커밋에 포함할 문서
11. 남은 위험
```

최종 원칙:

> 프로젝트 전체 변경은 PROJECT_CONTEXT·DECISIONS·contracts로 알리고,
> 각 담당의 실제 구현 진행 상황은 중앙화된 담당 Work log로 추적한다.

---

# 12. 구현·검증·배포 세부 규칙

이 절은 루트 `AGENTS.md`에서 분리한 세부 실행 기준이다. 각 담당 Codex는 실제 코드를 수정할 때 해당 언어와 영역의 규칙을 적용한다.

## 공통 구현 원칙

- MVP 핵심 흐름 밖의 기능과 불필요한 추상화를 추가하지 않는다.
- 요청과 직접 관련된 파일만 수정하고 주변 코드를 임의로 정리하지 않는다.
- 실행문은 한 줄에 하나만 작성하고 명확한 이름과 작은 책임 단위를 사용한다.
- 사용하지 않는 import, 죽은 코드, 주석 처리한 구현, 디버그 비밀값을 남기지 않는다.
- 새 의존성은 MVP에 반드시 필요한 경우에만 추가한다.
- 기존 동작을 바꾸는 정리나 리팩터링을 기능 변경과 섞지 않는다.

## Python

- 함수·변수·모듈은 `snake_case`, 클래스와 Pydantic 모델은 `PascalCase`, 상수는 `UPPER_SNAKE_CASE`를 사용한다.
- 공개 함수와 Agent 상태에 타입 힌트와 반환 타입을 작성한다.
- FastAPI route는 얇게 유지하고 비즈니스 로직은 service, tool, Agent node로 분리한다.
- 외부 호출에는 timeout과 구체적인 오류 처리를 둔다.
- LLM 추출 결과는 Pydantic 구조화 출력으로 검증한다.
- eligibility 판정은 자유 형식 LLM 출력으로 수행하지 않는다.
- 추출한 모든 변경에는 evidence를 연결한다.

## TypeScript·React

- 변수와 함수는 `camelCase`, 컴포넌트와 타입은 `PascalCase`, 상수는 `UPPER_SNAKE_CASE`를 사용한다.
- TypeScript를 사용하고 `any` 대신 DTO와 도메인 타입을 정의한다.
- API 접근, 결정론적 rule evaluation, UI 표현을 분리한다.
- API의 `snake_case` payload는 adapter에서 한 번만 변환하거나 DTO에 명시적으로 유지한다.
- 시민 프로필과 판정 결과를 서버 요청, 분석 로그, query string에 넣지 않는다.
- eligibility 설명은 결정론적 템플릿을 사용한다.

## Agent·문서 처리

- Agent는 HTML 완전성을 판단하고 필요한 첨부 도구를 선택한 뒤 결과를 평가해야 한다.
- 근거가 부족하면 `max_retry` 안에서 다른 경로를 시도하고, 해결되지 않으면 AgentRun으로 사람 검토를 요청한다.
- 노드와 도구 실행 로그를 남기되 시민 프로필이나 비밀값은 기록하지 않는다.
- 검증되지 않은 약한 근거를 자동 게시하지 않으며 사람 승인을 요구한다.
- legacy `.hwp`는 지원을 과장하지 않고 필요하면 사람 검토로 전환한다.

## 검증

- Python은 저장소 설정에 따라 `ruff check`, formatter check, `pytest`를 실행한다.
- 프론트엔드는 기존 `package.json` script의 type check, test, build를 실행한다.
- 공통 JSON 변경은 schema 자체 유효성, `$ref`, 대표 fixture, 재귀 rule을 검증한다.
- 새 formatter나 test framework를 팀 합의 없이 설치하지 않는다.
- 실행하지 않은 검증을 통과했다고 기록하지 않으며 실패·생략 항목을 명시한다.

## 배포

- 로컬 검증 후 현재 Terraform으로 관리하는 CloudFront, 비공개 S3, public ALB, private ECS Fargate, private RDS PostgreSQL, ECR, Secrets Manager와 NAT Gateway 구성을 사용한다.
- 현재 구조를 벗어난 Kubernetes나 별도 배포 플랫폼은 팀 합의 없이 추가하지 않는다.
- `.env.example`, CORS, API base URL, health check, HTTPS를 확인한다.
- 네트워크 실패 동작은 담당 Work log와 현재 구현을 따른다. 시민 PWA는 승인 정책 API 실패를 사용자에게 표시하고 정책 fixture로 대체하지 않으며, 관리자 화면의 기존 fixture fallback을 변경하려면 별도 합의한다.
- Git push 자동 배포는 없으므로 프론트는 build·S3 sync·CloudFront invalidation, 백엔드는 Docker build·ECR push·ECS rolling deployment를 수행한다.
- 백엔드 컨테이너와 AWS 배포 전 `docs/deployment/BACKEND_CONTAINER_HANDOFF.md`를 읽고 현재 준비 상태와 미구현 항목을 구분한다.

## Git 협업 세부사항

- 작업 전 최신 `main`을 받고 담당 브랜치에서 작업한다.
- 한 커밋에는 하나의 논리적 변경만 담고 관련 검증 후 올린다.
- 공용 브랜치를 force push하지 않고 충돌 해결 후 관련 검증을 다시 실행한다.
- `.env`, 자격 증명, dependency directory, 가상환경, build output, 실제 수집 원본은 커밋하지 않는다.
- 상세 커밋 제목은 루트 `AGENTS.md`의 형식을 따른다.
