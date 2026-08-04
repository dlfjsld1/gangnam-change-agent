> [!WARNING]
> Deprecated 문서입니다. 현재 프로젝트 기준은 아래 세 위치입니다.
> - `docs/PROJECT_CONTEXT.md`
> - `docs/DECISIONS.md`
> - `docs/contracts/`
# 강남 Change Agent — 팀 공통 계약

## 프로젝트 한 줄
강남구의 공고와 공공서비스 변경사항을 AI Agent가 탐색·분석하고, 승인된 정책 패키지를 사용자 기기에 배포한 뒤, 개인정보를 서버로 보내지 않고 기기 안에서 시민별 영향과 다음 행동을 계산하는 서비스다.

## 해커톤 조건
- 개발 기간: 2일
- 인원: 3명
- 필수 조건:
  1. 실제 AI Agent 구현
  2. 강남구 사회문제 해결
- 핵심 사회문제:
  - HTML·PDF·HWPX 등으로 흩어진 강남구 공공정보 때문에 시민이 조건 변경, 마감, 시설 운영 변경을 놓치는 정보 접근 격차

## 핵심 사용자 흐름
```text
강남구 공고 수집
→ Agent가 HTML 분석
→ 정보 부족 여부 판단
→ 첨부문서 형식에 맞는 도구 선택
→ 조건·기간·행동·근거 추출
→ 이전 공고와 비교
→ 근거 검증
→ 부족하면 재탐색
→ 해결되지 않으면 관리자 인계
→ 관리자 승인
→ 정책 패키지 배포
→ 사용자 기기에서 로컬 판정
→ 시민별 영향과 다음 행동 표시
```

## 절대 범위
반드시 구현:
- 실제 또는 실제 구조를 보존한 강남구 공고 1~2건
- HTML 분석
- HWPX 또는 PDF 첨부 분석 1건
- LangGraph 분기·재시도·관리자 인계
- 관리자 승인
- 정책 패키지 API
- 시민용 PWA
- 로컬 프로필
- YES / NO / UNKNOWN / STALE
- 사용자 A/B 비교
- 서버 개인정보 0건 화면

구현하지 않음:
- 로그인
- 자동 신청
- 실제 푸시
- 전국 정책
- 벡터 DB
- 온디바이스 LLM
- 모든 HWP/HWPX 지원
- 완전 자동 정책 버전 연결
- 복잡한 인프라

## 역할 경계
- Agent·Backend: `공고 → 정책 패키지`
- 시민용 PWA: `정책 패키지 → 로컬 판정 → 시민 화면`
- 관리자·통합·배포: `Agent 결과 → 관리자 승인 → 배포 및 전체 연결`

## 공통 정책 패키지 최소 계약
모든 팀원은 아래 필드를 기준으로 개발한다.

```json
{
  "policy_id": "demo-policy-v2",
  "policy_family_id": "demo-policy",
  "version": 2,
  "title": "청년 지원사업 변경",
  "category": "지원사업",
  "published_at": "2026-08-04",
  "effective_at": "2026-08-05",
  "deadline_at": "2026-09-10",
  "summary": "지원 연령이 확대되고 신청 마감이 앞당겨졌습니다.",
  "changes": [
    {
      "field": "age",
      "label": "지원 연령",
      "before": {"min": 19, "max": 34},
      "after": {"min": 19, "max": 39},
      "change_type": "expanded",
      "evidence_id": "evidence-1"
    }
  ],
  "eligibility_rule": {
    "and": [
      {"field": "residence", "operator": "equals", "value": "강남구"},
      {"field": "age", "operator": "between", "min": 19, "max": 39},
      {"field": "employment_status", "operator": "equals", "value": "unemployed"}
    ]
  },
  "required_profile_fields": [
    "residence",
    "age",
    "employment_status"
  ],
  "required_actions": [
    {
      "action_id": "check-employment",
      "label": "현재 고용 상태 확인",
      "priority": 1
    },
    {
      "action_id": "apply",
      "label": "2026-09-10까지 신청",
      "priority": 2
    }
  ],
  "evidence": [
    {
      "evidence_id": "evidence-1",
      "source_type": "HWPX",
      "document_name": "공고문.hwpx",
      "location": "2쪽 지원 대상 표",
      "quote": "지원 대상: 만 19세 이상 39세 이하",
      "source_url": "https://example.com"
    }
  ],
  "review": {
    "status": "approved",
    "reviewed_at": "2026-08-04T15:00:00+09:00"
  }
}
```

## 공통 API 계약
최소 기준이며 경로 변경 시 팀 전체에 즉시 공유한다.

```text
POST /api/notices/discover
POST /api/notices/{notice_id}/analyze
GET  /api/runs/{run_id}

GET  /api/reviews
GET  /api/reviews/{review_id}
POST /api/reviews/{review_id}/approve
POST /api/reviews/{review_id}/reject
POST /api/reviews/{review_id}/edit

GET  /api/policy-packages
GET  /api/policy-packages/{policy_id}
GET  /api/policy-packages/updates?after_version={version}
```

## 로컬 판정 규칙
- YES: 모든 필수 조건 충족
- NO: 하나 이상의 필수 조건 불충족
- UNKNOWN: 필요한 값이 없음
- STALE: 값은 있지만 유효기간 만료
- 숫자 확률 점수는 사용하지 않음

## 데모 사용자
사용자 A:
- residence = 강남구
- age = 35
- employment_status = unemployed
- employment_status는 오래된 값

예상:
- STALE → 질문 1개 → YES

사용자 B:
- residence = 송파구
- age = 35
- employment_status = unemployed

예상:
- NO

## 협업 규칙
1. 첫날 오후까지 실제 Agent 없이 고정 JSON으로 전체 흐름을 연결한다.
2. 이후 고정 JSON을 실제 Agent 결과로 교체한다.
3. 각 담당자는 자신의 폴더를 우선 소유하고, 다른 담당 폴더의 대규모 수정은 피한다.
4. 스키마나 API 변경은 임의로 하지 말고 공통 계약 파일에 반영한다.
5. 실제 데이터와 데모 데이터를 명확히 구분한다.
6. 구현보다 인프라나 디자인에 시간을 과하게 쓰지 않는다.
7. 네트워크·MCP 실패에 대비한 fallback JSON을 유지한다.
