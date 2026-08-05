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

## D-003 — 로컬 SQLite와 AWS PostgreSQL 공통 저장 계층

- Date: 2026-08-05
- Status: accepted
- Decision: SQLAlchemy 2와 Alembic을 공통으로 사용하고 DATABASE_URL로 SQLite와 PostgreSQL을 전환한다.
- AWS network: App Runner → VPC Connector → private RDS. 외부 공고 수집은 단일 NAT Gateway를 사용한다.
- Secret: RDS 비밀번호는 RDS가 Secrets Manager에서 관리하고, App Runner는 별도 DATABASE_URL secret ARN만 참조한다. 비밀 값은 Terraform state에 넣지 않는다.
- MVP storage: 현재 관리자 검토와 AgentRun DTO는 app_state JSON 테이블에 저장한다.
- Reason: API 계약 변경 없이 프로세스 재시작 시 상태를 보존하고 2일 MVP 배포 범위를 최소화한다.
- Upgrade trigger: 동시 수정 충돌이나 복잡한 DB 조회가 필요해지면 DTO별 정규화 테이블로 분리한다.
- Affected areas: backend, infra
