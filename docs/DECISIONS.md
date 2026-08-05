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
- Decision: HTML 본문과 동일 basename으로 제공되는 텍스트 PDF·HWPX를 먼저 파싱하고, 이미지와 스캔 PDF처럼 로컬 텍스트 추출이 불가능한 부분은 그다음 OpenAI OCR로 추출해 교차 검증한다. 필요한 문서 형식은 생략하지 않는다.
- Representative evidence priority: HTML, PDF, HWPX, image
- Comparison boundary: 동일 basename 첨부끼리는 원문 텍스트를 비교하고, 요약 HTML과 대표 첨부의 조건·기간·금액 비교는 구조화된 정책 조건 추출 단계에서 수행한다.
- Review rule: 로컬 추출과 필요한 OpenAI OCR 이후에도 남은 추출 실패 또는 내용 불일치는 `review_required` 사유로 남기고 결과를 임의로 폐기하지 않는다.
- Attachment transport: 첨부 URL은 강남구와 강남구 전자고시 호스트만 허용한다. 전자고시 호스트의 불완전한 인증서 체인에는 호스트 한정 예외를 적용하고 다운로드한 파일 signature를 검증한다.
- Reason: 배포 형식에 따른 누락과 파싱 오류를 교차 검증하고 관리자에게 근거 충돌을 노출하기 위함이다.
- Affected areas: backend, frontend/admin
- Contract impact: 현재 AgentRun의 `review_required`, `review_reason`, `unresolved_fields`로 표현 가능하므로 공통 schema 변경 없음

## D-005 — PDF 페이지별 로컬 추출과 OpenAI OCR 분기

- Date: 2026-08-05
- Status: accepted
- Decision: PDF는 페이지별 로컬 텍스트 추출을 먼저 시도한다. 의미 있는 문자가 부족해 로컬 추출이 불가능한 스캔 페이지는 그다음 이미지로 렌더링해 OpenAI Responses API OCR에 전달한다.
- Mixed PDF: 텍스트 페이지와 OCR 페이지를 원래 페이지 순서로 병합하고 각 페이지의 처리 방법을 기록한다.
- Image attachments: 로컬 텍스트 추출이 불가능하므로 앞선 로컬 문서 처리가 끝난 뒤 OpenAI Responses API OCR을 사용한다.
- Privacy: OpenAI에는 공개 공고와 공개 첨부문서만 전송하며 시민 프로필은 전송하지 않는다.
- Configuration: API key는 `OPENAI_API_KEY`, OCR 모델은 `OPENAI_OCR_MODEL` 환경변수로 주입한다.
- Escalation order: local extraction → required OpenAI OCR recovery → evidence comparison → administrator review.
- Reason: OpenAI OCR을 관리자 검토 직전의 제한된 복구 단계로 두어 API 비용과 지연을 줄이면서 사람 검토 전에 한 번 더 자동 복구하기 위함이다.
- Affected areas: backend
- Contract impact: 공통 API schema 변경 없음

## D-006 — 구조화 정책 후보와 결정론적 근거 검증

- Date: 2026-08-05
- Status: accepted
- Decision: 공개 공고 텍스트는 OpenAI Responses API의 Pydantic Structured Outputs로 `PolicyDraft` 후보를 추출하고, 백엔드가 이를 현재 `PolicyPackage` 계약으로 결정론적으로 조립한다.
- Evidence rule: 모델이 반환한 모든 인용은 지정한 원문 문서에 실제로 존재해야 하며, HTML 제목과 이미지 OCR의 핵심 문구 유사도가 기준보다 낮으면 검토 대상으로 전환한다.
- Field rule: 기존 registry에 없는 프로필 필드는 `pending` 상태로 포함하고 `AgentRun.unresolved_fields`에 기록한다. 승인된 정책으로 공개하지 않는다.
- Model: 기본 정책 추출 모델은 비용과 품질 균형을 위해 `gpt-5.6-terra`를 사용하고 `OPENAI_POLICY_MODEL`로 교체할 수 있다.
- Privacy: 모델 입력은 공개 공고와 공개 첨부 텍스트로 제한하며 시민 프로필은 포함하지 않는다.
- Reason: LLM은 구조화 후보 생성에만 사용하고 원문 근거·연산자·필드 승인 여부는 로컬 코드가 다시 검증하기 위함이다.
- Affected areas: backend, frontend/admin
- Contract impact: 현재 PolicyPackage와 AgentRun schema를 그대로 사용한다.
