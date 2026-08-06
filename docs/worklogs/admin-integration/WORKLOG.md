# Work Log

## Current status

- Current milestone: 최신 필드 검토·비공개 첨부 흐름 재배포와 전체 smoke
- Working: 실제 관리자 API 연결, FieldDefinitionReview 승인·수정·반려, 시민 질문·enum 선택지 편집, AgentRun 로그, 수동 새 공고 확인, 정책 Publish, 검토·공개 첨부 링크, CloudFront 관리자 웹
- Deployed baseline: ECS Fargate + ALB + CloudFront Backend API, RDS PostgreSQL, 관리자·시민 CloudFront, 공개 첨부 S3
- In progress: `review-attachments`와 최신 enum 편집 변경을 포함한 이미지·정적 웹 재배포 및 수집 → 승인 → 시민 반영 smoke
- Not implemented: 관리자 mutation API 운영 인증·접근 제한, Git push 자동 배포
- Blockers: 최신 Agent Backend PR의 main 병합 후 배포 필요

## Next actions

- [x] fixture 기반 FieldDefinitionProposal 목록과 상세 검토 화면을 만든다.
- [x] 원문 evidence, 제안 필드, 기존 canonical field 후보를 함께 표시한다.
- [x] 승인·수정·반려 동작을 로컬 fixture 상태로 먼저 연결한다.
- [x] AgentRun의 review_required, review_reason, unresolved_fields와 실행 로그를 표시한다.
- [x] 관리자 API 준비 후 fixture adapter를 실제 API adapter로 연결한다.
- [x] 관리자 API adapter를 실제 실행·검토·정책 API에 연결한다.
- [x] 새 공고 확인 버튼을 수동 크롤링 API에 연결하고 처리 결과를 새로고침한다.
- [ ] 승인된 PolicyPackage 공개 흐름과 시민 PWA 연결을 검증한다.
- [x] 관리자 웹·시민 PWA·백엔드 기본 구성을 AWS에 배포한다.
- [x] enum 질문의 판정값과 시민 표시 문구를 추가·수정·삭제해 승인한다.
- [ ] 최신 Backend image와 Admin build를 배포하고 비공개 검토 첨부·enum 승인·시민 공개를 smoke한다.

## Completion criteria

- 관리자가 제안 필드의 근거를 보고 승인·수정·반려할 수 있다.
- AgentRun의 사람 검토 사유와 미해결 필드가 화면에 표시된다.
- 승인된 정책만 시민 API에 공개되는 흐름을 확인할 수 있다.
- API 연결 실패 상태가 관리자에게 명확히 표시된다.
- 관리자 화면은 브라우저에서, 시민 화면은 설치 가능한 PWA로 동작한다.
- 관련 build와 로컬 end-to-end smoke check가 통과한다.

## Dependencies

- 최신 배포는 Agent Backend PR 병합 후 Docker image와 Admin 정적 build를 함께 갱신한다.
- 시민 profile catalog 소비는 Citizen PWA 담당 작업이며 관리자 UI ownership으로 가져오지 않는다.

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition-proposal.schema.json
- docs/contracts/field-definition-review.schema.json
- docs/contracts/api.md
- docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md

## Change history

### 2026-08-06 — enum 시민 질문·선택지 수정 승인

#### Summary

필드 검토 화면에서 기존 시민 질문과 함께 enum의 판정값·시민 표시 문구를 추가·수정·삭제하고 `approved_field.allowed_values`로 승인할 수 있게 했다. 빈 enum 또는 값·표시 문구가 비어 있는 선택지는 승인 전에 차단한다.

#### Contract impact

기존 FieldDefinition과 수정 승인 API를 그대로 사용하며 새 endpoint나 schema는 추가하지 않았다.

#### Validation

- 관리자 TypeScript·Vite production build: passed
- 백엔드 수정 승인·PolicyPackage 반영 test: passed
- 백엔드 pytest: 87 passed, 6 warnings

### 2026-08-06 — 필드 검토 원본 공고·첨부 연결

#### Summary

필드 검토 항목을 선택하면 연결된 Agent 실행의 원본 공고와 첨부를 조회해 검토 패널 안에서 바로 열 수 있게 했다. 첨부 링크는 `review_url ?? public_url ?? url` 순서로 사용한다. 연결된 실행과 정책 ID를 따라 실제 정책명을 표시하고, 검토 탭을 `1. 필드 검토 → 2. 정책 승인·공개` 단계형 헤더로 바꿔 다음 흐름을 안내한다. Hero 문구, 중복 요약 카드 4개와 API URL 표시를 제거하고 `새 공고 확인`을 단계 헤더 오른쪽에 배치했다. 중복 상단 링크를 제거하고 실제 작업·오류 메시지를 최상단 상태 줄에 표시한다. 실행 상세의 내부 run ID는 숨기고 펼침 상태 화살표로 교체했다.

#### Changed files

- `frontend/admin/src/App.tsx`
- `frontend/admin/src/styles.css`

#### Tests

- `frontend/admin`: `npm.cmd run build` — passed

### 2026-08-06 — 정책 검토 S3 원본 첨부 연결

#### Summary

정책 카드에서 연결된 Agent 실행 상세를 조회하고 `review_url ?? public_url ?? url` 순서로 첨부를 열 수 있게 했다. 검토용 S3 링크는 비공개 15분 URL임을 표시하고, ECS에는 `review-attachments/*` 읽기·쓰기 권한과 prefix 설정을 추가했다.

#### Changed files

- `frontend/admin/src/App.tsx`
- `frontend/admin/src/types.ts`
- `frontend/admin/src/styles.css`
- `infra/attachments.tf`
- `infra/main.tf`

#### Contract impact

`docs/DECISIONS.md` D-009와 첨부·API 계약에 승인 전 검토 URL을 추가했다.

#### Tests

- `frontend/admin`: `npm.cmd run build` passed
- `infra`: `terraform fmt -recursive` passed
- `infra`: `terraform validate` passed

#### Remaining work

- Terraform apply, backend image 배포, Admin 정적 배포
- 배포 환경에서 수집 → S3 review prefix → Admin 링크 열기 smoke 확인

### 2026-08-05 — 관리자 검토 단계 탭 통합

#### Summary

필드 검토와 정책 최종 승인·공개를 하나의 작업영역 탭으로 통합하고, 실행 기록과 원본 공고를 필드 탭의 접이식 상세로 이동했다. 마지막 필드 처리 후 정책 탭으로 자동 전환하며 각 단계의 승인 버튼 문구를 구분했다.

#### Changed files

- `frontend/admin/src/App.tsx`
- `frontend/admin/src/styles.css`

#### Tests

- `frontend/admin`: `npm.cmd run build` passed

### 2026-08-05 — 필드 수정 승인 API 연결 복구

#### Summary

현재 백엔드가 수정된 `approved_field`를 `/approve`에서 처리하는 구현에 맞춰 `수정 후 승인` 요청 경로를 복구했다.

#### Tests

- `frontend/admin`: `npm.cmd run build` passed

### 2026-08-05 — 완료된 필드 검토 큐 제거

#### Summary

필드 검토 목록을 pending 상태로만 조회하고 승인·수정 승인·반려 성공 시 완료 항목을 즉시 제거한 뒤 다음 대기 항목을 선택하도록 수정했다.

#### Tests

- `frontend/admin`: `npm.cmd run build` passed

### 2026-08-05 — 관리자 검토 화면 재구성

#### Summary

관리자 업무 순서에 맞춰 현황, 필드 검토, 실행 추적, 정책 공개 화면을 재구성하고 반응형 레이아웃과 GSAP 진입 모션을 적용했다. `수정 후 승인` 요청이 계약의 `/edit` 경로를 호출하도록 API 연결 오류를 수정했다.

#### Changed files

- `frontend/admin/src/App.tsx`
- `frontend/admin/src/styles.css`
- `frontend/admin/src/api.ts`
- `frontend/admin/package.json`
- `frontend/admin/package-lock.json`

#### Contract impact

없음. 기존 관리자 API 계약을 그대로 사용한다.

#### Tests

- `frontend/admin`: `npm.cmd run build` passed
- `git diff --check`: passed
- 브라우저 시각 검증: 실행 환경에 연결 가능한 브라우저가 없어 미실행

### 2026-08-05 — Backend 관리자 API 연결

#### Summary

승인·반려 버튼의 API 경로를 계약에 맞추고 fixture fallback을 유지한 채 LIVE API 동작을 연결했다.

#### Verification

- `npm.cmd run build`: passed
- 로컬 관리자 페이지 및 API: HTTP 200
### 2026-08-05 — 수동 새 공고 확인 버튼

#### Summary

관리자가 버튼을 누르면 `POST /api/notice-discovery-runs`로 강남구 공식 게시판 크롤링을 요청하고, 새 공고의 Agent 실행 결과와 검토 목록을 다시 표시하도록 연결했다. 실행 중 중복 요청을 막고 신규 공고 없음과 실패 상태를 안내한다.

#### Dependency

- Backend의 `Feat: 새 공고 수동 확인 API 추가` 변경이 main과 배포 환경에 반영되어야 한다.

#### Verification

- `frontend/admin`: `npm.cmd run build` passed

### 2026-08-04 — fixture 기반 관리자 검토 화면 구현

#### Summary

FieldDefinitionReview 목록·상세, evidence, canonical field 후보, 승인·수정·반려와 AgentRun 로그를 구현했다. 관리자 API가 없거나 네트워크가 실패하면 동일 DTO 형태의 demo fixture로 전환한다.

#### Verification

- `frontend/admin`: `npm.cmd run build` 통과

### 2026-08-04 — 다음 작업 큐 확정

#### Summary

fixture 기반 검토 화면부터 실제 API 통합과 AWS 배포까지의 순서와 완료 조건을 정리했다.

### 2026-08-04 — 초기 동기화 로그 생성

#### Summary

최신 동적 프로필 결정에 맞춰 관리자 검토 범위를 기록했다.

### 2026-08-05 — Terraform AWS DB·Backend 배포 구성

#### Summary

Private RDS PostgreSQL, Secrets Manager, ECR, App Runner VPC Connector와 외부 공고 접근용 단일 NAT Gateway를 Terraform으로 구성했다. 비밀 값이 Terraform state에 들어가지 않는 2단계 배포 절차를 문서화했다.

#### Verification

- terraform fmt -recursive: passed
- terraform init -backend=false: passed
- terraform validate: passed
- docker build (backend/Dockerfile): passed
- 실제 AWS plan/apply: 미실행, AWS 계정과 배포 origin 필요

### 2026-08-05 — 서울 리전 ECS backend 배포

#### Summary

서울 리전에서 지원되지 않는 App Runner 대신 기존 VPC, private RDS, ECR을 재사용하는 ECS Fargate 배포로 전환했다. CloudFront HTTPS, public ALB, private ECS task 경로로 backend를 배포하고 Secrets Manager의 DATABASE_URL로 PostgreSQL에 연결했다.

#### Verification

- Terraform validate: passed
- Terraform plan after apply: No changes
- backend pytest: 54 passed
- Docker build and ECR push: passed
- ECS desired/running: 1/1, steady state
- ALB target health: healthy
- HTTPS health and API smoke: HTTP 200
- CloudWatch: Alembic PostgreSQL migration and Uvicorn startup passed
### 2026-08-05 — 관리자 API 검토·공개 흐름 연결

#### Summary

관리자 화면을 AgentRun 목록·상세와 관리자용 PolicyPackage 목록 API에 연결하고 정책 승인·반려 결과를 즉시 반영하도록 구현했다. 기존 필드 검토와 API 실패 시 fixture fallback은 유지했다.

#### Changed files

- `frontend/admin/src/api.ts`
- `frontend/admin/src/App.tsx`
- `frontend/admin/src/types.ts`

#### Contract impact

없음. 기존 `docs/contracts/api.md` 경로와 payload를 사용한다.

#### Tests

- `frontend/admin`: `npm.cmd run build` passed
- `frontend/citizen`: `npm.cmd run build` passed
- `backend`: `python -m pytest tests/test_main.py tests/test_deployment_smoke.py` — 17 passed

#### Remaining work

- 배포 API를 대상으로 관리자 승인 후 시민 PWA 공개까지 브라우저 E2E smoke 확인
- 관리자·시민 프론트 배포 환경에 `VITE_API_BASE_URL` 설정

### 2026-08-05 — 프로덕션 API 주소 연결

#### Summary

관리자 프로덕션 빌드의 `VITE_API_BASE_URL`을 Terraform `backend_url` 출력값으로 설정했다.

#### Tests

- `terraform output -raw backend_url`: `https://d25409t9vvq1vj.cloudfront.net`
- `frontend/admin`: `npm.cmd run build` passed
- 빌드 JavaScript에서 CloudFront 주소 확인

### 2026-08-05 — 관리자·시민 프론트 AWS 배포

#### Summary

관리자와 시민 프론트를 각각 비공개 S3와 CloudFront OAC로 배포했다. Terraform이 두 프론트 origin을 백엔드 CORS에 자동 반영하도록 연결했다.

#### Changed files

- `infra/frontend.tf`
- `infra/main.tf`
- `infra/outputs.tf`
- `docs/DEPLOYMENT.md`

#### Tests

- `terraform fmt -recursive`: passed
- `terraform validate`: passed
- `terraform apply`: 11 added, 1 changed, 1 replaced
- 최종 `terraform plan -detailed-exitcode`: No changes
- 관리자 CloudFront: HTTP 200
- 시민 CloudFront: HTTP 200
- 관리자·시민 origin의 API CORS header 확인: passed

#### Remaining work

- 연결 가능한 브라우저 환경에서 실제 UI smoke 확인

### 2026-08-05 — 배포 백엔드 API 이미지 갱신

#### Summary

관리자 화면이 fixture fallback으로 전환된 원인은 배포 ECR 이미지가 `/api/agent-runs`와 `/api/admin/policy-packages` 구현 이전 버전이었던 것이다. 현재 백엔드 이미지로 ECR `latest`를 갱신하고 ECS rolling deployment를 완료했다.

#### Tests

- backend Docker build: passed
- ECR push digest: `sha256:9298f4d6afbbdd4fa166e5a59aaa69e89c4f2218b783b70f73a39c66c763e57f`
- ECS service stable: passed
- `GET /api/agent-runs`: HTTP 200, admin CORS passed
- `GET /api/admin/policy-packages`: HTTP 200, admin CORS passed

### 2026-08-05 — 공개 근거 첨부 S3·Admin 통합

#### Summary

전용 비공개 S3와 CloudFront OAC를 구성하고 ECS task role에 `public-attachments/` 업로드 권한과 archive 환경변수를 연결했다. Admin 실행 상세는 원본 공고와 첨부를 표시하고, 정책 승인 후 연결된 실행을 재조회해 `public_url`로 갱신하며 409와 503을 구분한다.

#### Tests

- `terraform -chdir=infra validate`: passed
- `frontend/admin`: `npm.cmd run build` passed
- AWS plan/apply 및 실제 S3 업로드: 미실행

### 2026-08-05 — OpenAI Secret 연결과 공개첨부 인프라 배포

#### Summary

기존 Secrets Manager JSON의 `DATABASE_URL`과 `OPENAI_API_KEY`를 ECS secret 환경변수로 각각 연결했다. 공개첨부 S3·CloudFront와 ECS 업로드 task role도 Terraform으로 적용했다.

#### Tests

- `terraform -chdir=infra apply`: passed
- 최종 `terraform -chdir=infra plan -detailed-exitcode`: No changes
- ECS task definition revision 3: RUNNING, desired/running 1/1
- 배포 backend `/health`: `status=ok`
- 실제 OpenAI API 호출과 S3 첨부 업로드: 미실행
