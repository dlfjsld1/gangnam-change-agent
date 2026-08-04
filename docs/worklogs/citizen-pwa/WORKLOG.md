# Work Log

## Current status

- Current milestone: 설치 가능한 PWA 보일러플레이트
- Working: manifest, service worker, 동적 프로필 타입, IndexedDB 저장 인터페이스, 확정된 판정 규칙 문서
- In progress: required_profile_fields 기반 질문과 실제 매칭 화면 연결
- Not implemented: 사용자 A/B 전환 UI, 질문 답변 UI, API adapter
- Blockers: MVP 연산자 중 in, contains, exists와 OR 구현 필요

## Next actions

- [ ] matcher에 `in`, `contains`, `exists`, 재귀 `AND/OR`를 구현하고 판정 우선순위 테스트를 추가한다.
- [ ] `unknown-question-smoke.json`을 matcher와 질문 선택 흐름에 연결한다.
- [ ] `required_profile_fields`를 DynamicQuestion 입력과 연결한다.
- [ ] 답변을 IndexedDB에 저장하고 저장 직후 정책을 다시 판정한다.
- [ ] `stale-refresh-smoke.json`을 연결해 STALE 갱신 질문을 UNKNOWN 신규 질문보다 먼저 표시한다.
- [ ] 승인된 정책 패키지만 읽는 API adapter와 fixture fallback을 연결한다.
- [ ] 사용자 A/B 프로필 전환과 결과·해야 할 일 화면을 완성한다.

## Completion criteria

- equals, in, between, contains, exists와 재귀 AND/OR가 계약대로 판정된다.
- UNKNOWN fixture가 질문 화면으로 이어지고 답변 후 즉시 재판정된다.
- STALE 질문이 UNKNOWN 질문보다 먼저 선택된다.
- 프로필은 IndexedDB에만 저장되고 서버 요청·로그·URL에 포함되지 않는다.
- 승인되지 않은 정책 패키지는 시민 화면에 표시되지 않는다.
- 관련 테스트와 production build가 통과한다.

## Dependencies

- 첫 다섯 작업은 현재 fixture와 계약만으로 진행할 수 있다.
- API adapter의 실제 호출 전환은 백엔드의 승인 정책 API를 사용한다.
- 계약 충돌 시 matcher를 임의 변경하지 말고 `docs/contracts/`를 먼저 갱신한다.

## Current contracts

- docs/contracts/policy-package.schema.json
- docs/contracts/field-definition.schema.json

## Change history

### 2026-08-04 — 다음 작업 큐 확정

#### Summary

matcher 연산자 완성부터 질문·IndexedDB·재판정·API 연결까지의 순서와 완료 조건을 정리했다.

### 2026-08-04 — 동적 프로필 계약 반영

#### Summary

고정 프로필 대신 Record<string, ProfileValue> 타입과 결정론적 AND 규칙 평가 골격을 추가했다.

#### Tests

- 현재 추가 모듈의 프론트 단위 테스트 없음
- 이전 PWA production build 확인됨
