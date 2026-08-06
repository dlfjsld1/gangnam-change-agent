# Project Context

## Current product

Gangnam Change Agent는 강남구 공고와 첨부문서의 변경을 Agent가 근거와 함께 구조화하고, 관리자 승인 후 시민 기기에서만 개인별 영향을 판정하는 2일 해커톤 MVP다.

## Current end-to-end flow

```text
강남구 공고 수집
→ HTML 본문 완전성 확인
→ 필요한 첨부파일 도구 선택
→ PDF/HWPX 추출
→ 이전 공고 비교
→ 근거 검증과 제한된 재시도
→ 미해결 시 관리자 검토 요청
→ 관리자 승인
→ 정책 패키지 공개
→ 시민 기기에서 로컬 판정
```

크롤링이나 요약만으로 Agent 구현이 완료된 것으로 보지 않는다. Agent는 정보 완전성 판단, 도구 선택, 결과 평가, 재시도 또는 사람 검토 전환을 실행 로그로 보여야 한다.

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
- 팀이 승인한 기본 프로필 필드 정의는 공개 catalog API로 제공하되 시민 답변은 기기에만 저장한다.
- HumanHandoff는 별도 API가 아니라 AgentRun의 review_required, review_reason, unresolved_fields로 표현한다.

## Privacy boundary

- 시민의 나이, 거주, 고용, 소득, 가구, 건강·장애 정보와 전체 로컬 프로필은 서버로 보내지 않는다.
- 시민별 판정 결과도 서버, 분석 로그, URL query에 포함하지 않는다.
- 공개 공고, 정책 패키지, 관리자 검토 상태, 시민 정보가 없는 Agent 실행 로그만 서버에서 다룬다.
- 시민 프로필은 IndexedDB에 저장하며 완벽한 보안을 주장하지 않는다.
- 사용자 안내에는 “중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.”라는 표현을 사용한다.

## MVP boundary

현재 저장소에는 Scrapling 정적 Fetcher 수집, HTML·PDF·HWPX·이미지 분석, 필요한 OpenAI OCR, LangGraph 실행, 이전 정책 diff, 근거 검증, FieldDefinitionReview, PolicyPackage 승인·공개, 시민 로컬 판정과 관리자 검토 UI가 구현돼 있다. 관리자 웹, 시민 PWA와 Backend API의 AWS 기본 배포도 확인했다.

최신 구현은 기본 프로필 canonical field catalog와 문맥형 질문·enum 선택지 수정 승인을 포함한다. Citizen PWA가 `GET /api/profile-fields`를 소비해 임시 관심 분야 정의를 제거하고, `잘 모르겠어요`를 저장하지 않는 `UNKNOWN` 유지 동작과 자주 쓰는 정류장 입력을 연결하는 작업이 남아 있다. 최신 변경을 AWS에 다시 배포한 뒤 수집 → 검토 → 승인 → 시민 반영 전체 smoke도 수행해야 한다.

MVP에서 제외하는 범위는 주기 크롤링, 실시간 정책 push, 관리자 mutation API 운영 인증, 바이너리 HWP 파서와 다수 정책을 합친 전역 질문 우선순위 최적화다.

## MVP public sources

- 정책·혜택: 강남구청 통합 공고 시스템의 고시공고와 채용공고
- 생활권·정류장: 강남구 주민센터 공통 새소식 게시판
- 통합 공고는 `not_ancmt_mgt_no`, 주민센터 새소식은 게시물 경로 ID를 source ID로 사용한다.
- MVP 주민센터 수집은 정류장 데모가 있는 삼성1동부터 시작하고 같은 게시판 구조로 확장한다.
