# Work Log

## Current status

- Current milestone: 온보딩부터 정책 상세까지 이어지는 시민 PWA 데모
- Working: manifest, service worker, 동적 프로필 타입, IndexedDB 저장, 재귀 판정 matcher, 온보딩·질문 답변과 UNKNOWN/STALE 재판정, 카드 피드와 로컬 숨기기, 승인 정책 API fallback, 입력 정보 요약과 선택 관심 분야 저장
- In progress: 홈 화면 피드백 반영과 관심 분야를 여러 공고 정렬에 연결할 시점 검토
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
- [x] 필수 정보 입력 뒤 요약 확인과 선택 관심 분야 입력 흐름을 제공한다.
- [x] 대상이 아닌 `NO` 정책 카드를 홈과 즐겨찾기에서 숨긴다.
- [x] 정책 상세에서 evidence의 원문 공고 URL로 이동하는 버튼을 제공한다.
- [x] 공고 카드의 정보 간격과 강조 단계를 정리하고 YES 상태 문구의 체크 기호를 제거한다.
- [x] 승인 정책 evidence의 S3 또는 공식 원문 URL을 새 탭에서 안전하게 연다.

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

### 2026-08-05 공개 첨부 S3 링크 계약 반영

#### Summary

최신 `main`의 공개 첨부 계약을 반영했다. 시민 PWA는 S3에 직접 업로드하거나 별도 API를 호출하지 않고, 승인 정책 evidence의 `source_url`을 그대로 사용한다. 이 URL은 승인 뒤 S3 또는 CloudFront 고정 URL일 수 있으며 새 탭에서 안전하게 연다.

#### Tests

- Pending: `npm.cmd run build`

### 2026-08-05 공고 카드 가독성 정리

#### Summary

공고 카드의 상태·분야·제목·변경값·설명·해야 할 일·상세 버튼 사이 여백과 글자 크기를 고르게 다듬었다. `대상 가능성 높음` 상태의 체크 기호를 제거해 상태 배지가 더 차분하게 보이도록 했다.

#### Tests

- 브라우저 확인: 사용자 C 카드에서 정리된 간격과 상태 배지 확인
- `npm.cmd run build`: passed

### 2026-08-05 원문 공고 이동 버튼

#### Summary

정책 상세 화면의 변경 근거 아래에 원문 공고를 여는 카드형 링크 버튼을 추가했다. 정책 JSON의 첫 evidence `source_url`을 새 탭으로 열며, 현재 API에 첨부파일 목록이 없으므로 첨부파일은 원문 공고 페이지에서 확인하도록 안내한다.

#### Tests

- 브라우저 확인: 사용자 C의 정책 상세에서 원문 공고 링크 렌더링과 `source_url` 확인
- `npm.cmd run build`: passed

### 2026-08-05 대상 아닌 공고 숨김

#### Summary

로컬 결정론적 판정이 `NO`인 정책은 홈과 즐겨찾기 목록에서 제외했다. 아직 정보가 부족한 `UNKNOWN`과 갱신이 필요한 `STALE` 정책은 질문을 계속 보여주며, 대상이 아닌 정책만 빈 안내 화면으로 처리한다.

#### Tests

- 브라우저 확인: 사용자 B(강남구 외 거주) 선택 시 카드 0개와 빈 안내 표시
- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 인트로 요약과 선택 관심 분야

#### Summary

필수 정책 질문을 모두 입력한 뒤 저장될 정보를 요약해서 보여주고, 선택적으로 관심 분야 여섯 가지를 고를 수 있게 했다. 관심 분야는 다른 프로필 값과 같이 이 기기 IndexedDB에만 저장하며, 현재 정책의 대상 판정에는 사용하지 않는다.

#### Tests

- 브라우저 확인: 기본 4개 입력 → 요약 → 관심 분야 선택 → 홈 이동 → 내 정보에서 선택값 표시
- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 실제 승인 정책 API 연동 확인

#### Summary

로컬 FastAPI의 `/health`와 승인 정책 조회 API를 확인하고, 시민 PWA가 fixture 안내 없이 API에서 받은 승인 정책 카드를 표시하는 것을 확인했다. 시민 프로필과 시민별 판정 결과는 API 요청에 포함하지 않았다.

#### Tests

- `GET http://localhost:8000/health`: `{"status":"ok"}` 확인
- `GET http://localhost:8000/api/policy-packages`: 승인 정책 배열 1건 확인
- 브라우저 확인: 사용자 A 선택 후 API 정책 카드 표시, fixture 안내 미표시
- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed

### 2026-08-05 탭 전환 부드럽게 연결

#### Summary

홈, 즐겨찾기, 내 정보 탭을 바꿀 때 새 화면이 180ms 동안 아주 살짝 나타나도록 연결했다. 하단 탐색의 선택 표시는 크기 변화 없이 색만 전환하며, reduced motion 환경에서는 움직임을 사용하지 않는다.

#### Tests

- `npm.cmd run build`: passed
- 브라우저 확인: 사용자 C 선택 후 즐겨찾기 탭 전환 정상 동작

### 2026-08-05 헤더와 하단 아이콘 정리

#### Summary

클로버처럼 보이던 상단 기호를 작은 종 아이콘으로 바꾸고, 하단 탐색의 이모지를 둥근 선형 SVG 아이콘으로 통일했다. 내 정보에는 어른 둘과 아이를 표현한 가족 아이콘을 사용했다.

#### Tests

- `npm.cmd run build`: passed

### 2026-08-05 발표용 데모 리모컨 분리

#### Summary

홈 피드 안에 있던 데모 전환 버튼을 제거하고, 앱 바깥의 세로형 A/B/C 프로필 리모컨으로 옮겼다. 각 데모 프로필에서 변경한 답변은 이 기기 IndexedDB에 사용자별로 따로 저장한다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed
- 브라우저 확인: 앱 바깥 리모컨에서 사용자 C 전환 후 대상 가능 결과 표시

### 2026-08-05 홈·즐겨찾기 헤더 숫자 강조

#### Summary

홈과 즐겨찾기 화면의 상단 제목을 같은 네이비 헤더 리듬으로 맞추고, 제목 아래 공고 수의 숫자만 밝은 파란색과 큰 크기로 강조했다. 별도 박스는 사용하지 않아 차분한 톤을 유지한다.

#### Tests

- `npm.cmd run build`: passed

### 2026-08-05 인트로 거주 동 입력 다듬기

#### Summary

첫 정보 입력 화면의 가로 여백을 정리하고, `거주 지역` 대신 `살고 있는 동`을 받도록 바꿨다. 강남구 밖의 동은 팝업 없이 입력칸 아래에서 안내하며, 기존 정책의 강남구 단위 판정은 유지한다.

#### Tests

- `npm.cmd test`: 8 passed
- `npm.cmd run build`: passed
- 브라우저 확인: `서초동` 입력 시 입력칸 아래에 안내 문구가 표시됨

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
