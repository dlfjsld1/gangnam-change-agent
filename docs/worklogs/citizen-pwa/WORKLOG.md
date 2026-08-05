# Work Log

## Current status

- Current milestone: 온보딩부터 정책 상세까지 이어지는 시민 PWA 데모
- Working: manifest, service worker, 동적 프로필 타입, IndexedDB 저장, 재귀 판정 matcher, 온보딩·질문 답변과 UNKNOWN/STALE 재판정, 카드 피드와 로컬 숨기기, 승인 정책 API fallback
- In progress: 홈 화면 피드백 반영과 실제 통합 smoke check
- Not implemented: 없음
- Blockers: 없음

## Next actions

- [x] matcher에 `in`, `contains`, `exists`, 재귀 `AND/OR`를 구현하고 판정 우선순위 테스트를 추가한다.
- [x] `unknown-question-smoke.json`을 matcher와 질문 선택 흐름에 연결한다.
- [x] `required_profile_fields`를 DynamicQuestion 입력과 연결한다.
- [x] 답변을 IndexedDB에 저장하고 저장 직후 정책을 다시 판정한다.
- [x] `stale-refresh-smoke.json`을 연결해 STALE 갱신 질문을 UNKNOWN 신규 질문보다 먼저 표시한다.
- [x] 카드형 홈 피드와 기기 내 카드 숨기기·복원 동작을 구현한다.
- [x] 승인된 정책 패키지만 읽는 API adapter와 fixture fallback을 연결한다.
- [x] 사용자 A/B 프로필 전환과 결과·해야 할 일 화면을 완성한다.
- [x] 정책 변경·마감일·해야 할 일·근거를 보여주는 카드 상세 화면을 구현한다.
- [x] 정책 카드를 세로 스냅 피드로 표시한다.
- [x] 첫 실행 온보딩과 정책 기반 내 정보 설정 화면을 구현한다.
- [x] 인트로 개인정보 원칙과 저장된 내 정보 조회 화면을 구현한다.
- [x] 공고 즐겨찾기 저장과 즐겨찾기 탭을 구현한다.
- [x] 첫 실행 인트로를 개인정보 원칙 중심으로 정리하고 다시 보기 경로를 제공한다.
- [x] 시민 기기의 프로필·즐겨찾기·숨김 상태를 삭제하고 인트로로 돌아가는 경로를 제공한다.

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

### 2026-08-05 — 재귀 판정 matcher 완성

#### Summary

`equals`, `in`, `between`, `contains`, `exists`와 재귀 `AND/OR`를 구현하고, 계약의 AND/OR 우선순위를 검증하는 Node 내장 테스트를 추가했다.

#### Tests

- `npm.cmd test`: 4 passed
- `npm.cmd run build`: passed

### 2026-08-05 — UNKNOWN 질문 선택 연결

#### Summary

판정 결과가 `UNKNOWN`이면 승인된 required profile field 중 규칙에 필요한 첫 미입력 필드를 질문으로 선택하도록 연결했다.

#### Tests

- `npm.cmd test`: 5 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 질문 답변과 로컬 재판정 연결

#### Summary

fixture 정책의 승인된 required profile field를 DynamicQuestion 입력으로 표시하고, 답변을 IndexedDB에 저장한 뒤 즉시 로컬에서 다시 판정하도록 연결했다.

#### Tests

- `npm.cmd test`: 6 passed
- `npm.cmd run build`: passed

### 2026-08-05 — STALE 갱신 질문 우선순위 연결

#### Summary

만료된 답변이 있으면 신규 미입력 필드보다 먼저 갱신 질문을 선택하고, 화면에서 갱신 이유를 안내하도록 연결했다.

#### Tests

- `npm.cmd test`: 7 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 카드형 홈 피드 프로토타입

#### Summary

참고 이미지의 차분한 네이비 헤더와 큰 정책 카드를 바탕으로 모바일 우선 홈 피드를 구현했다. 관심 없는 정책 카드는 IndexedDB에만 숨김 상태를 저장하고 다시 볼 수 있다.

#### Tests

- 브라우저 확인: 카드 숨기기와 다시 보기 동작 확인
- `npm.cmd test`: 7 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 승인 정책 API fallback 연결

#### Summary

승인 정책 API를 먼저 호출하고, 요청 실패·비정상 응답 시 demo fixture를 사용하도록 adapter를 연결했다. API 응답에서는 승인 상태 정책만 시민 화면에 전달한다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 사용자 A/B 데모와 결과 화면

#### Summary

발표용 사용자 A/B 프로필을 기기 내 임시 상태로 전환하고, 대상 가능성이 높은 정책에는 우선순위별 해야 할 일을 표시하도록 연결했다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 정책 상세 화면

#### Summary

카드에서 정책 상세 화면을 열어 변경 내용, 신청 마감일, 해야 할 일, 공고 근거를 확인하고 닫을 수 있게 구현했다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 세로 스냅 정책 피드

#### Summary

정책 카드가 여러 개일 때 모바일 화면에서 한 장씩 아래로 넘겨 보도록 세로 스냅 피드를 적용했다.

#### Tests

- `npm.cmd run build`: passed

### 2026-08-05 — 카드 피드 스크롤 보완

#### Summary

고정 높이 내부 스크롤을 제거하고 일반 페이지 스크롤의 proximity 스냅으로 변경해 카드 잘림과 상단 스크롤 끊김을 줄였다. 중복된 개인정보 안내 박스는 제거하고 헤더 안내만 유지했다.

#### Tests

- `npm.cmd run build`: passed

### 2026-08-05 — 온보딩과 내 정보 설정

#### Summary

첫 실행에서 개인정보 로컬 저장 원칙을 안내하고, 승인 정책의 required profile field를 순서대로 입력한 뒤 홈 피드로 이동하도록 연결했다. 하단 내 정보 탭에서 다시 수정할 수도 있다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 인트로 개인정보 안내와 내 정보 조회

#### Summary

기획의 개인정보 원칙 문구를 첫 실행 인트로에 반영하고, `내 정보` 탭에서 IndexedDB에 저장한 승인 프로필 필드와 값을 먼저 확인한 뒤 수정 화면으로 이동하도록 연결했다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 즐겨찾기 공고

#### Summary

하단 `전체 변경`을 `즐겨찾기`로 바꾸고, 공고 카드의 원형 별 버튼으로 즐겨찾기를 저장·해제할 수 있게 했다. 즐겨찾기 탭에는 별을 찍은 공고만 표시하며, 이 상태도 시민 기기 IndexedDB에만 저장한다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 개인정보 원칙 인트로 개선

#### Summary

첫 실행 인트로를 네이비 서비스 소개, 개인정보 원칙, 세 가지 로컬 처리 안내, 시작 버튼의 흐름으로 정리했다. 저장한 프로필이 있어도 `내 정보`에서 서비스 소개를 다시 볼 수 있다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 — 로컬 데이터 삭제와 인트로 복귀

#### Summary

`내 정보`에 이 기기에서만 저장한 프로필, 즐겨찾기, 숨김 카드 상태를 한 번에 삭제하는 확인 버튼을 추가했다. 삭제 후 첫 실행 인트로로 돌아가며, 서버 요청이나 개인정보 전송은 없다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed
- 브라우저 확인: 초기화된 로컬 저장 상태에서 인트로 표시 확인
