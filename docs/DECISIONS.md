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
- Field rule: 기존 registry의 `approved` 필드는 재사용한다. 없는 프로필 필드는 `pending` FieldDefinition과 FieldDefinitionProposal을 만들고 `AgentRun.unresolved_fields`에 기록한다. 이미 `pending` 또는 `rejected`인 registry 필드는 중복 제안하지 않으며 승인된 정책으로 공개하지 않는다.
- Model: 기본 정책 추출 모델은 비용과 품질 균형을 위해 `gpt-5.6-terra`를 사용하고 `OPENAI_POLICY_MODEL`로 교체할 수 있다.
- Privacy: 모델 입력은 공개 공고와 공개 첨부 텍스트로 제한하며 시민 프로필은 포함하지 않는다.
- Reason: LLM은 구조화 후보 생성에만 사용하고 원문 근거·연산자·필드 승인 여부는 로컬 코드가 다시 검증하기 위함이다.
- Affected areas: backend, frontend/admin
- Contract impact: 현재 PolicyPackage와 AgentRun schema를 그대로 사용한다.

## D-007 — 로컬 SQLite와 배포 PostgreSQL

- Date: 2026-08-05
- Status: accepted
- Decision: 로컬 개발은 SQLite를 사용하고 AWS 배포 환경은 PostgreSQL을 사용한다. 백엔드는 SQLAlchemy 저장소 계층을 공유하며 `DATABASE_URL`로 dialect를 전환한다.
- Stored data: 공개 SourceNotice, AgentRun, PolicyPackage 후보, FieldDefinitionProposal과 관리자 검토 상태
- Excluded data: 시민 프로필과 시민별 판정 결과는 서버 데이터베이스에 저장하지 않는다.
- Reason: 로컬 개발 설정은 가볍게 유지하면서 배포 환경의 동시 접근과 영속성을 지원하기 위함이다.
- Affected areas: backend, frontend/admin, infra
- Contract impact: 공통 JSON Schema 변경 없음. 실제 Agent 실행 및 관리자 API는 같은 저장소 계층을 사용한다.

## D-008 — 승인된 공개 근거 첨부의 S3 고정 URL 제공

- Date: 2026-08-05
- Status: accepted
- Decision: 관리자 최종 승인 시 PolicyPackage evidence가 실제로 참조하는 강남구 공식 공개 첨부만 S3 `public-attachments/` 경로에 복사하고 고정 공개 URL로 evidence를 갱신한다.
- Privacy boundary: 시민 프로필과 시민별 판정 결과는 S3에 저장하지 않는다. 검토 전 첨부와 정책 근거로 사용하지 않은 첨부도 공개 archive 대상이 아니다. 개인정보 가능성을 나타내는 파일명은 자동 공개를 차단한다.
- Storage metadata: SourceNotice attachment에 원본 URL, S3 key, 공개 URL과 SHA-256을 함께 저장한다.
- Delivery: 시민 PWA와 관리자 화면은 PolicyPackage evidence의 고정 URL을 사용한다. 버킷 업로드는 AWS IAM Role로 수행하며 access key를 코드나 환경 파일에 저장하지 않는다.
- Reason: 공식 사이트 링크 변경 후에도 승인 당시 근거를 재현하고, PWA 사용자가 만료 없는 공개 첨부 링크를 열 수 있게 한다.
- Affected areas: backend, frontend/citizen, frontend/admin, infra
- Contract impact: 관리자 실행 상세 응답에 `source_notice`가 추가되며 기존 PolicyPackage evidence 구조는 유지한다.

## D-009 — 승인 전 첨부의 비공개 S3 관리자 검토

- Date: 2026-08-06
- Status: accepted
- Previous design: 승인 전에는 공식 원본 URL만 표시하고 정책 최종 승인 시 evidence 첨부를 S3에 저장한다.
- New design: Agent 실행이 공고를 수집하면 파싱 성공 여부와 관계없이 공식 첨부를 S3 `review-attachments/`에 비공개 저장한다. 관리자 실행 상세는 만료되는 presigned `review_url`을 제공하며, 최종 승인 시 evidence 첨부만 기존 `public-attachments/`에 공개 archive한다.
- Privacy boundary: 검토 첨부는 CloudFront 공개 경로에서 제외하고 ECS task role만 읽고 쓴다. 시민 프로필과 시민별 판정 결과는 저장하지 않으며 presigned URL은 DB에 저장하지 않는다.
- Reason: 파싱 실패·OCR 실패·근거 불일치 정책도 관리자가 수집 당시 원본 첨부로 검증할 수 있어야 한다.
- Affected areas: backend, frontend/admin, infra
- Affected contracts: `docs/contracts/api.md`, `docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md`

## D-010 — 기본 프로필 필드 catalog와 추천 필드 분리

- Date: 2026-08-06
- Status: accepted
- Decision: 백엔드는 PWA 첫 온보딩에 필요한 승인 canonical field 정의를 독립 registry에 seed하고 `GET /api/profile-fields`로 공개한다. `residence`, `age`, `employment_status`, `frequent_bus_stops`는 core, `interest_categories`는 optional이다.
- Eligibility boundary: `residence`, `age`, `employment_status`만 Agent의 자격 조건 field registry에서 재사용한다. `frequent_bus_stops`는 주변 영향 확인용, `interest_categories`는 추천·정렬용이므로 EligibilityRule이나 PolicyPackage의 `required_profile_fields`에 자동으로 넣지 않는다.
- Interest values: `youth_jobs`, `housing_living`, `welfare_care`, `culture_sports`, `transport_facilities`, `education_family`를 승인된 선택값으로 사용한다.
- Privacy: 서버에는 필드 정의만 저장한다. 시민이 입력한 기본정보와 관심 분야는 IndexedDB에만 저장하며 서버로 전송하지 않는다.
- Approval: MVP 기본 seed는 팀 합의로 approved 상태이며 AgentRun이나 가짜 FieldDefinitionProposal을 생성하지 않는다. 관리자 생성·수정 UI는 후속 범위다.
- Reason: PWA의 임시 하드코딩과 Agent canonical key의 불일치를 막으면서 추천 정보가 자격 판정에 잘못 사용되는 것을 방지하기 위함이다.
- Affected areas: backend, frontend/citizen
- Contract impact: additive `ProfileFieldCatalogItem` schema와 `GET /api/profile-fields` API를 추가한다. 기존 FieldDefinition과 PolicyPackage schema는 변경하지 않는다.
