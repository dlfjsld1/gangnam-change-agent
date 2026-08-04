# Work Log

## Current status

- Current milestone: fixture 기반 Backend 보일러플레이트
- Working: health API, 승인 정책 fixture API, FieldDefinition·EligibilityRule·PolicyPackage·AgentRun 계약
- In progress: 계약 기반 Pydantic 모델 정렬
- Not implemented: Scrapling, HWPX/PDF 파서, DB, Agent 실행 로그
- Blockers: 실제 강남구 공고와 첨부파일 후보 확정 필요

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition.schema.json
- docs/contracts/field-definition-proposal.schema.json

## Change history

### 2026-08-04 — 동적 필드 보일러플레이트

#### Summary

새 조건의 FieldDefinitionProposal과 관리자 검토 필요 상태를 위한 최소 인터페이스를 추가했다.

#### Tests

- pytest: 7 passed
- ruff check: passed
