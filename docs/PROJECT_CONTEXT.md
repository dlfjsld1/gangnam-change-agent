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
- HumanHandoff는 별도 API가 아니라 AgentRun의 review_required, review_reason, unresolved_fields로 표현한다.

## Privacy boundary

- 시민의 나이, 거주, 고용, 소득, 가구, 건강·장애 정보와 전체 로컬 프로필은 서버로 보내지 않는다.
- 시민별 판정 결과도 서버, 분석 로그, URL query에 포함하지 않는다.
- 공개 공고, 정책 패키지, 관리자 검토 상태, 시민 정보가 없는 Agent 실행 로그만 서버에서 다룬다.
- 시민 프로필은 IndexedDB에 저장하며 완벽한 보안을 주장하지 않는다.
- 사용자 안내에는 “중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.”라는 표현을 사용한다.

## MVP boundary

현재는 fixture 기반 보일러플레이트다. 실제 Scrapling, HWPX/PDF 파싱, LangGraph 실행, 관리자 승인 UI, 시민 질문 화면은 각 담당 브랜치에서 구현한다.
