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

## D-004 — 동일 문서의 형식별 추출과 교차 검증

- Date: 2026-08-05
- Status: accepted
- Decision: HTML 본문과 동일 basename으로 제공되는 PDF·HWPX·이미지를 가능한 범위에서 모두 파싱하며, 확장자 우선순위로 다른 형식을 생략하지 않는다.
- Representative evidence priority: HTML, PDF, HWPX, image
- Comparison boundary: 동일 basename 첨부끼리는 원문 텍스트를 비교하고, 요약 HTML과 대표 첨부의 조건·기간·금액 비교는 구조화된 정책 조건 추출 단계에서 수행한다.
- Review rule: 형식별 추출 실패 또는 내용 불일치는 `review_required` 사유로 남기고 결과를 임의로 폐기하지 않는다.
- Attachment transport: 첨부 URL은 강남구와 강남구 전자고시 호스트만 허용한다. 전자고시 호스트의 불완전한 인증서 체인에는 호스트 한정 예외를 적용하고 다운로드한 파일 signature를 검증한다.
- Reason: 배포 형식에 따른 누락과 파싱 오류를 교차 검증하고 관리자에게 근거 충돌을 노출하기 위함이다.
- Affected areas: backend, frontend/admin
- Contract impact: 현재 AgentRun의 `review_required`, `review_reason`, `unresolved_fields`로 표현 가능하므로 공통 schema 변경 없음

## D-005 — PDF 페이지별 로컬 추출과 OpenAI OCR 분기

- Date: 2026-08-05
- Status: accepted
- Decision: PDF는 페이지별로 로컬 텍스트를 먼저 추출하고, 의미 있는 문자가 부족한 스캔 페이지만 이미지로 렌더링해 OpenAI Responses API OCR에 전달한다.
- Mixed PDF: 텍스트 페이지와 OCR 페이지를 원래 페이지 순서로 병합하고 각 페이지의 처리 방법을 기록한다.
- Image attachments: 이미지 첨부는 OpenAI Responses API OCR을 사용한다.
- Privacy: OpenAI에는 공개 공고와 공개 첨부문서만 전송하며 시민 프로필은 전송하지 않는다.
- Configuration: API key는 `OPENAI_API_KEY`, OCR 모델은 `OPENAI_OCR_MODEL` 환경변수로 주입한다.
- Reason: 텍스트 PDF의 불필요한 API 비용과 지연을 피하면서 스캔·혼합 PDF를 처리하기 위함이다.
- Affected areas: backend
- Contract impact: 공통 API schema 변경 없음
