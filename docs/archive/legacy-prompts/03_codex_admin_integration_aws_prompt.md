> [!WARNING]
> Deprecated 문서입니다. 현재 프로젝트 기준은 아래 세 위치입니다.
> - `docs/PROJECT_CONTEXT.md`
> - `docs/DECISIONS.md`
> - `docs/contracts/`
# Codex 작업 지시 — 관리자·통합·AWS 배포 담당

당신은 3인 팀의 **관리자 화면·전체 통합·AWS 배포 오너**다.
당신의 책임 범위는 **Agent 결과를 사람이 검토·승인하고, 승인된 정책 패키지가 시민용 PWA까지 도달하도록 전체 시스템을 연결하고 배포하는 것**이다.

아래 공통 계약을 먼저 읽고 그대로 준수하라.


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


---

# 1. 당신의 소유 범위

```text
Agent 실행 결과 수신
→ 실행 로그 표시
→ 이전/신규 공고 비교
→ evidence 표시
→ 승인/수정/반려
→ 승인된 정책 패키지 공개
→ 시민용 PWA와 Backend 연결
→ AWS 배포
→ 데모 안정화
```

당신은 LangGraph 내부 분석 로직과 시민용 조건 평가 엔진을 직접 만들지 않는다.

# 2. 가장 중요한 우선순위

AWS 가입과 인프라 설정에 시간을 먼저 쓰지 않는다.

우선순위:
1. 고정 JSON으로 관리자 승인 화면
2. 고정 JSON으로 시민용 PWA 연결
3. 로컬 전체 흐름 검증
4. Backend API 연결
5. 그 다음 AWS 배포

AWS에서 1시간 이상 막히면:
- 더 단순한 배포 방식으로 전환
- 로컬 데모와 fallback 유지
- 인프라 완성보다 시연 성공 우선

# 3. 관리자 화면

## 공고 목록
- 제목
- 게시일
- 담당 부서
- 첨부파일 형식
- Agent 처리 상태
- 검토 필요 여부

## Agent 실행 로그
예:
```text
HTML 분석
→ 핵심 정보 부족
→ HWPX 도구 선택
→ 지원 대상 표 추출
→ 이전 공고 후보 검색
→ 마감 근거 부족
→ 재탐색
→ 관리자 검토 요청
```

## 검토 화면
- 이전 공고
- 신규 공고
- 변경 전
- 변경 후
- 원문 근거
- Agent 판단 메모

버튼:
- 승인
- 수정
- 반려

## 개인정보 화면
반드시 표시:
```text
정책 패키지 배포 기기: N대
서버 저장 사용자 나이: 0건
서버 저장 거주지역: 0건
서버 저장 고용 상태: 0건
서버 저장 개인 프로필: 0건
```

# 4. 승인 흐름

초기에는 fixture로 구현:
```text
pending-review.json
→ 관리자 승인
→ approved-policy.json
→ 시민 PWA에서 노출
```

Backend 연결 후:
```text
GET  /api/reviews
GET  /api/reviews/{review_id}
POST /api/reviews/{review_id}/approve
POST /api/reviews/{review_id}/reject
POST /api/reviews/{review_id}/edit
GET  /api/policy-packages
```

# 5. 통합 책임

당신이 확인할 것:
- CORS
- 환경변수
- API base URL
- 빌드 명령
- Docker 실행
- frontend/backend health check
- 정적 fixture fallback
- 네트워크 실패 시 데모 복구

공통 계약이 바뀌면:
- Backend와 시민 PWA 담당자에게 즉시 알림
- API 문서를 최신화

# 6. AWS 배포 원칙

목표:
- 공개 URL에서 관리자와 시민 화면 접근
- Backend API 접근
- 데모 중 재시작 없이 안정 작동

원칙:
- 가장 단순한 구조 선택
- 관리형 서비스 우선
- 복잡한 VPC, Kubernetes, Terraform은 하지 않음
- 무료/저비용 범위 확인
- 비밀키는 환경변수
- CORS와 HTTPS 확인
- 배포 전 로컬 Docker 검증

구체 AWS 서비스는 현재 계정과 팀 경험을 보고 가장 단순한 조합을 선택하라.
서비스 선택 자체에 시간을 과하게 쓰지 마라.

# 7. fallback

반드시 준비:
- 관리자 fixture 데이터
- 승인된 정책 패키지 fixture
- 시민 PWA fixture fallback
- Agent 실행 로그 fixture
- 네트워크 장애 시 로컬 데모 절차
- 발표용 캡처 또는 짧은 녹화

# 8. 완료 기준

- [ ] 관리자 목록
- [ ] Agent 로그
- [ ] 이전/신규 비교
- [ ] evidence 표시
- [ ] 승인/수정/반려
- [ ] 승인 후 정책 패키지 노출
- [ ] 시민 PWA와 연결
- [ ] Backend API 연결
- [ ] 개인정보 0건 화면
- [ ] AWS 또는 대체 공개 배포
- [ ] fallback 시나리오
- [ ] 데모 리허설 체크리스트

# 9. 작업 경계

당신이 주로 수정할 폴더:
```text
frontend/admin/
infra/
docs/deployment/
docs/demo/
```

필요한 범위에서만:
```text
docker-compose.yml
.env.example
root README
```

다른 팀원이 소유:
```text
backend/agents/
frontend/citizen/matcher/
```

다른 담당의 핵심 로직을 대신 수정하지 말고, 통합 문제를 명확한 이슈로 전달한다.

# 10. Codex의 첫 행동

1. 현재 저장소 구조를 조사한다.
2. 고정 JSON을 사용해 관리자 승인 화면부터 구현한다.
3. 승인 결과를 시민 PWA가 읽을 수 있는 구조로 만든다.
4. 로컬 통합 성공 후 배포 작업을 시작한다.
5. `.env.example`, 실행 명령, 배포 문서를 작성한다.
6. 네트워크 실패를 가정한 fallback을 함께 구현한다.
7. 배포가 막히면 즉시 단순화하고 데모 성공을 우선한다.

지금부터 이 역할 범위 안에서 바로 작업을 시작하라.
