# Project Context

## Current product

Gangnam Change Agent는 강남구 공고와 첨부문서의 변경을 Agent가 근거와 함께 구조화하고, 관리자 승인 후 시민 기기에서만 개인별 영향을 판정하는 2일 해커톤 MVP다.

## Team ownership

- Agent·백엔드: 공고 수집·문서 분석·LangGraph·근거 검증·정책 패키지 API
- 시민용 PWA: 동적 로컬 프로필·IndexedDB·결정론적 매칭·추가 질문
- 관리자·통합: 필드 제안 검토·승인/반려·실행 로그·통합·배포

## Current contract

- 정책 패키지의 required_profile_fields는 승인 상태를 가진 객체 배열이다.
- EligibilityRule은 equals, in, between, contains, exists와 AND/OR만 지원한다.
- 시민 프로필은 Record<string, ProfileValue>로 IndexedDB에만 저장한다.
- 시민 판정은 YES, NO, UNKNOWN, STALE만 사용하며 LLM이 판정하지 않는다.
- 새 필드는 Agent가 제안하고 관리자 승인 후에만 시민 앱에 배포한다.
- HumanHandoff는 별도 API가 아니라 AgentRun의 review_required, review_reason, unresolved_fields로 표현한다.

## MVP boundary

현재는 fixture 기반 보일러플레이트다. 실제 Scrapling, HWPX/PDF 파싱, LangGraph 실행, 관리자 승인 UI, 시민 질문 화면은 각 담당 브랜치에서 구현한다.

## Deployment architecture

- Local persistence: SQLite via DATABASE_URL
- AWS persistence: private RDS for PostgreSQL via App Runner VPC Connector
- Shared data layer: SQLAlchemy 2 and Alembic
- Secrets: RDS-managed password and App Runner DATABASE_URL reference in Secrets Manager
- Container path: ECR to App Runner; private subnet internet egress uses one MVP NAT Gateway
