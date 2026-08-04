# Gangnam Change Agent

강남구 공개 공고의 변경사항을 Agent가 근거와 함께 구조화하고, 승인된 정책 패키지를 시민 기기에서 로컬로 판정하는 2일 해커톤 MVP입니다.

## 역할

- Agent·Backend: 공고에서 검토 대기 정책 패키지까지 담당
- 시민용 PWA: 승인된 정책 패키지에서 로컬 시민 결과까지 담당
- 관리자·통합: 검토 대기 정책 패키지에서 승인·공개·배포까지 담당

공통 계약은 docs/contracts/policy-package.schema.json과 docs/contracts/api.md에 있습니다.

## 실행

### Backend

PowerShell에서 backend로 이동한 뒤 다음 순서로 실행합니다.

1. python -m venv .venv
2. .\.venv\Scripts\Activate.ps1
3. pip install -e ".[dev]"
4. uvicorn app.main:app --reload

http://localhost:8000/health 에서 상태를 확인합니다.

### 시민용 PWA

PowerShell에서 frontend/citizen으로 이동한 뒤 다음 순서로 실행합니다.

1. Copy-Item .env.example .env
2. npm.cmd install
3. npm.cmd run dev

기본 주소는 http://localhost:5173 입니다. manifest와 service worker가 포함되어 있어 브라우저에서 설치 가능한 독립 실행형 시민용 PWA입니다.

### 관리자용 브라우저 앱

PowerShell에서 frontend/admin으로 이동한 뒤 다음 순서로 실행합니다.

1. Copy-Item .env.example .env
2. npm.cmd install
3. npm.cmd run dev

기본 주소는 http://localhost:5174 입니다. 관리자는 설치형 앱이 아닌 일반 브라우저 웹앱으로 운영합니다.

## 검증

- Backend: backend에서 pytest 실행
- 시민용 PWA: frontend/citizen에서 npm.cmd run build 실행
- 관리자 앱: frontend/admin에서 npm.cmd run build 실행

## 개인정보 원칙

시민의 나이, 거주지, 고용 상태, 로컬 프로필 및 판정 결과는 서버 API로 보내지 않습니다. demo-data/user-a.json과 demo-data/user-b.json은 프론트 로컬 개발용 가상 데이터입니다.

## 브랜치 분리

공통 계약, fixture, 최소 API, 시민 PWA 빌드, 관리자 앱 빌드가 모두 확인된 최신 main에서 다음 브랜치를 생성합니다.

- feat/agent-backend
- feat/citizen-pwa
- feat/admin-deploy

보일러플레이트에는 Agent 분석, 시민 규칙 판정, 관리자 승인 동작, AWS 배포를 포함하지 않습니다.
