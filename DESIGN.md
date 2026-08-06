# Design

## Source of truth

- Status: Active
- Last refreshed: 2026-08-05
- Primary product surfaces: 시민용 PWA 홈, 정책 카드 피드, 프로필 질문
- Evidence reviewed: 사용자 제공 모바일 참고 이미지 2장, `frontend/citizen/src/App.tsx`, `frontend/citizen/src/styles.css`, `demo-data/approved-policy.json`

## Brand

- Personality: 차분하고 명확하며 신뢰할 수 있는 공공 서비스
- Trust signals: “내 정보는 이 기기 안에서만”이라는 쉬운 안내, 상태가 분명한 카드, 과장하지 않는 문구
- Avoid: 복잡한 대시보드, 과도한 경고색, 개인정보 수집을 연상시키는 표현

## Product goals

- Goals: 시민이 자신과 관련된 정책 변화를 빠르게 확인하고 필요한 질문에 답하게 한다.
- Non-goals: 서버에 시민 프로필·판정 결과를 저장하거나, 관리자 기능을 시민 화면에 노출하지 않는다.
- Success signals: 첫 화면에서 관련 변화·현재 확인 상태·다음 행동을 이해할 수 있다.

## Personas and jobs

- Primary personas: 강남구 생활 정보와 지원 정책 변화를 확인하려는 시민
- User jobs: 관련 변화를 넘겨 보고, 필요한 정보만 기기 안에서 입력하고, 관심 없는 항목을 숨긴다.
- Key contexts of use: 모바일 브라우저와 설치형 PWA의 짧은 확인 세션

## Information architecture

- Primary navigation: 홈, 즐겨찾기, 내 정보
- Core routes/screens: 정책 카드 피드 홈, 카드 상세, 개인정보 원칙을 설명하는 첫 실행 인트로·정보 입력, 저장한 값 확인·수정이 가능한 로컬 프로필
- Content hierarchy: 개인 관련 변화 수 → 개인정보 안내 → 한 장씩 넘기는 정책 카드 피드 → 하단 탐색

## Design principles

- 큰 제목과 짧은 문장으로 현재 상태를 먼저 알린다.
- 정책 하나를 하나의 큰 카드로 보여 주고, 한 화면에 한 가지 다음 행동만 강조한다.
- 숨기기와 프로필 저장은 기기 안에서만 처리하며 그 사실을 숨기지 않는다.
- Tradeoffs: 승인 정책 API에 연결할 수 없으면 임의의 공고를 대신 보여 주지 않고, 연결 실패 안내를 표시한다.

## Visual language

- Color: 깊은 네이비 배경, 선명한 블루 CTA, 흰 카드, 옅은 하늘색 안내 영역, 성공 상태의 녹색
- Typography: 한국어 가독성을 우선한 굵은 제목과 편안한 본문 크기
- Spacing/layout rhythm: 모바일 20~24px 여백, 카드 간 16px, 큰 헤더와 둥근 상단 모서리
- Shape/radius/elevation: 20~28px 둥근 카드, 얕은 테두리와 부드러운 그림자
- Motion: 정책 카드는 일반 스크롤을 방해하지 않는 proximity 세로 스냅을 사용하며, reduced motion 환경에서는 스냅을 해제한다.
- Imagery/iconography: 단순한 선형 기호와 텍스트 라벨을 함께 사용한다.

## Components

- Existing components to reuse: `DynamicQuestion`, 로컬 프로필·matcher 모듈
- New/changed components: 정책 카드, 상태 배지, 원형 즐겨찾기 버튼, 개인정보 원칙·3가지 안내를 담은 인트로, 첫 실행 정보 입력, 저장 프로필 목록·수정·로컬 데이터 삭제, 하단 탐색
- Variants and states: YES/NO/UNKNOWN/STALE, 숨김, 즐겨찾기, 빈 상태, 질문 저장 중
- Token/component ownership: 시민 PWA의 CSS 변수와 `frontend/citizen/**`

## Accessibility

- Target standard: WCAG 2.1 AA 수준의 대비와 읽기 쉬운 크기
- Keyboard/focus behavior: 모든 버튼은 키보드 포커스와 명확한 focus ring을 제공한다.
- Contrast/readability: 네이비 배경에는 흰 텍스트, 상태는 색과 문구를 함께 쓴다.
- Screen-reader semantics: 카드와 탐색에는 명확한 제목·버튼 라벨을 사용한다.
- Reduced motion and sensory considerations: 장식적 자동 이동을 사용하지 않는다.

## Responsive behavior

- Supported breakpoints/devices: 360px 이상 모바일 우선, 넓은 화면에서는 480px 폭의 중앙 열
- Layout adaptations: 카드 피드는 세로 스크롤, 하단 탐색은 화면 하단에 유지
- Touch/hover differences: 터치 가능한 요소는 최소 44px 높이를 확보한다.

## Interaction states

- Loading: 로컬 프로필을 불러오는 짧은 상태 문구
- Empty: 숨긴 카드를 다시 볼 수 있는 빈 상태
- Error: 저장 실패 시 현재 프로필을 유지하고 안내한다.
- Success: 답변 저장 뒤 상태와 다음 카드 행동을 즉시 갱신한다.
- Disabled: 저장 중에는 답변 버튼을 비활성화한다.
- Offline/slow network, if applicable: 공고 API에 연결할 수 없다는 안내를 표시하고, 기기에 저장한 개인정보는 유지한다.

## Content voice

- Tone: 친절하고 단정하며 시민에게 책임을 넘기지 않는다.
- Terminology: “관련된 변화”, “확인 필요”, “이 기기 안에서만”을 우선 사용한다.
- Microcopy rules: 상태는 짧게 설명하고, 숨기기처럼 되돌릴 수 있는 행동은 결과를 분명히 알린다.

## Implementation constraints

- Framework/styling system: React, TypeScript, Vite, CSS
- Design-token constraints: 외부 UI 라이브러리 없이 CSS 변수로 구현한다.
- Performance constraints: 외부 이미지·폰트 의존성을 추가하지 않는다.
- Compatibility constraints: 시민 프로필과 숨김 상태는 IndexedDB에만 저장한다.
- Test/screenshot expectations: matcher 테스트와 production build를 유지하고 모바일 브라우저로 확인한다.

## Open questions

- [x] 다중 공고 카드 피드 / Citizen PWA / 2026-08-05: 여러 공고는 현재 카드와 다음 카드 일부를 세로 캐러셀로 이어서 보여 주고, 휠·터치 스와이프 한 번마다 부드럽게 다음 카드로 회전한다. 첫 카드는 헤더 아래에 살짝 겹치며, 발표용 `공고 4개 보기`는 프로필을 바꾸면 해제된다.

- [x] 탭 전환 모션 / Citizen PWA / 2026-08-05: 홈·즐겨찾기·내 정보는 180ms의 짧은 페이드·상향 전환으로 연결하고, reduced motion 환경에서는 움직이지 않는다.

- [x] 헤더·하단 탐색 아이콘 / Citizen PWA / 2026-08-05: 운영체제 이모지 대신 둥근 선형 SVG를 사용한다. 상단은 작은 종, 내 정보는 어른 둘과 아이를 표현한 가족 아이콘을 쓴다.

- [x] 발표용 프로필 전환 / Citizen PWA / 2026-08-05: 시민 화면 내부에는 넣지 않고, 데스크톱 시연 시 앱 바깥의 세로형 리모컨에서 A/B/C 로컬 프로필을 전환한다.

- [x] 인트로 거주지 용어 / Citizen PWA / 2026-08-05: 일반적인 거주 지역 대신 강남구 동을 묻고, 강남구 밖의 동은 팝업 없이 입력칸 바로 아래에서 안내한다.

- [x] 인트로 선택 정보 / Citizen PWA / 2026-08-05: 필수 정책 질문 뒤에 입력값을 먼저 요약하고, 관심 분야는 선택 입력으로만 받는다. 관심 분야는 로컬에만 저장하며 현재 대상 판정에는 사용하지 않는다.

- [x] 원문·첨부 근거 링크 / Citizen PWA / 2026-08-05: 정책 상세에서 원문 공고와 evidence 첨부파일을 분리된 카드형 링크로 표시하며, 모든 링크는 새 탭에서 안전하게 연다.

- [x] 내 정보 관리 행동 위계 / Citizen PWA / 2026-08-05: 기본 정보와 선택 정보 편집은 2열 카드로 묶고, 서비스 소개는 보조 한 줄 버튼으로 둔다. 로컬 데이터 삭제는 오조작을 줄이도록 화면 아래의 작은 위험 동작으로 분리한다.

- [x] 빈 피드 화면 / Citizen PWA / 2026-08-05: 빈 상태는 오류처럼 보이는 문장만 두지 않고, 옅은 하늘색 선형 아이콘·한 줄 제목·짧은 설명·필요한 경우 다음 행동 버튼을 둔 카드로 통일한다.

- [x] 세부 화면 뒤로가기 / Citizen PWA / 2026-08-05: 하단 탭처럼 최상위 화면에는 뒤로가기를 두지 않는다. 공고 상세는 스크롤 중에도 유지되는 상단 돌아가기 헤더를 사용하고, 내 정보 수정·추가 정보 입력은 `← 내 정보`로 돌아가는 경로를 명시한다.

- [x] 내 정보 상단 정보 위계 / Citizen PWA / 2026-08-05: 저장 위치와 용도를 반복하는 보조 문구는 제거하고, 개인정보 처리 원칙 안내와 실제 저장값을 바로 보여 준다. 일반 텍스트는 검정 대신 차콜 회색을 기본으로 사용하며, 네이비는 서비스 헤더·강조에만 남긴다.

- [x] 내 정보 관리 메뉴 단순화 / Citizen PWA / 2026-08-05: 여러 개의 강조 카드 대신 기본 정보·추가 정보·서비스 소개를 하나의 얇은 설정 목록으로 묶는다. 파란 CTA는 이 화면에서 사용하지 않고 저장값을 읽는 흐름을 우선한다.

- [ ] 카드 상세 화면의 정보 범위와 원문 evidence 노출 방식 / 시민 PWA 담당 / 중간
- [ ] 실제 정책 API 연결 후 여러 카드의 정렬 기준 / 백엔드·시민 PWA 담당 / 중간
