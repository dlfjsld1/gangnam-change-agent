# Work Log

## Current status

- Current milestone: 설치 가능한 PWA 보일러플레이트
- Working: manifest, service worker, 동적 프로필 타입, IndexedDB 저장 인터페이스, 확정된 판정 규칙 문서
- In progress: required_profile_fields 기반 질문과 실제 매칭 화면 연결
- Not implemented: 사용자 A/B 전환 UI, 질문 답변 UI, API adapter
- Blockers: MVP 연산자 중 in, contains, exists와 OR 구현 필요

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition.schema.json

## Change history

### 2026-08-04 — 동적 프로필 계약 반영

#### Summary

고정 프로필 대신 Record<string, ProfileValue> 타입과 결정론적 AND 규칙 평가 골격을 추가했다.

#### Tests

- 현재 추가 모듈의 프론트 단위 테스트 없음
- 이전 PWA production build 확인됨
