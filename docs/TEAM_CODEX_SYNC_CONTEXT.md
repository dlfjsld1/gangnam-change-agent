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
   ├─ contracts/
   │  ├─ policy-package.schema.json
   │  ├─ field-definition.schema.json
   │  └─ api.md
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

공통 JSON이나 API가 바뀌면 구현보다 계약 문서를 먼저 수정한다.

## `docs/worklogs/`

담당별 현재 구현 상태와 변경 이력을 기록한다.

Work log는 프로젝트 전체 기획을 공지하는 파일이 아니다.

- `PROJECT_CONTEXT.md`: 현재 기획
- `DECISIONS.md`: 공통 결정과 이유
- `contracts/`: 공유되는 코드 계약
- `WORKLOG.md`: 각 담당의 실제 구현 상태

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

### 관리자·통합

- 새 필드 제안 표시
- 원문 근거 표시
- canonical key 중복 후보 표시
- 질문·허용값 수정
- 승인·반려
- 승인된 필드만 시민 API에 공개

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
