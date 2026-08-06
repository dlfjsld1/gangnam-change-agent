# Backend Container Deployment Handoff

## Purpose and ownership

이 문서는 관리자·통합·배포 담당과 그 Codex가 백엔드 Dockerfile을 만들고 AWS
실행 환경을 연결할 때 필요한 현재 문맥이다.

- Agent·백엔드 담당은 FastAPI 실행 코드, Python 의존성, API, DB repository와
  `/health` 동작을 책임진다.
- 관리자·통합·배포 담당은 `backend/Dockerfile`, 컨테이너 build/run, PostgreSQL
  연결, AWS 환경변수·secret, HTTPS와 배포 health check를 책임진다.
- Dockerfile 작업은 Agent topology, parsing, OCR, policy extraction 로직을
  수정하는 권한을 의미하지 않는다.

## Required reading order

1. `AGENTS.md`
2. 이 문서
3. `docs/DECISIONS.md`의 D-005, D-006, D-007
4. `docs/contracts/api.md`
5. `docs/contracts/PUBLIC_ATTACHMENT_FRONTEND_INTEGRATION.md`
6. `docs/worklogs/admin-integration/WORKLOG.md`

API 구현 상태를 판단해야 할 때만
`docs/worklogs/agent-backend/WORKLOG.md`의 `Current status`와 `Next actions`를
추가로 확인한다.

## Current deployable boundary

현재 FastAPI 애플리케이션은 다음 명령으로 실행된다.

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

현재 컨테이너 smoke 범위:

- `GET /health`가 `{"status":"ok"}`를 반환한다.
- `GET /api/profile-fields`가 PWA 온보딩용 승인 canonical field 정의를 반환한다.
- 승인 정책 fixture 조회 API가 실행된다.
- `POST /api/agent-runs`가 LangGraph를 실행하고 결과를 DB에 저장한다.
- `POST /api/notice-discovery-runs`가 강남구 공식 게시판을 Scrapling Fetcher로
  조회하고 미처리 공고를 Agent에 넣는다.
- `GET /api/agent-runs/{run_id}`가 저장된 AgentRun을 조회한다.
- FieldDefinitionReview 목록·승인·수정·반려 API가 DB 검토 상태를 변경한다.
- AgentRun 목록과 실행별 정책·필드 제안·검토 묶음 조회 API를 제공한다.
- 관리자 PolicyPackage 목록·상세 API는 pending/rejected 상태도 조회할 수 있다.
- PolicyPackage 승인·반려 API가 검토 완료 상태를 저장한다.
- 연결된 모든 field review가 승인된 PolicyPackage만 시민 조회 API에 공개된다.
- FastAPI lifespan에서 SQLAlchemy schema를 초기화한다.
- OpenAI client는 Agent 요청 전에는 외부 API를 호출하지 않는다.
- 수집한 공식 첨부를 비공개 `review-attachments/`에 저장하고 관리자 상세 조회에서 단기 presigned URL을 제공한다.
- 최종 승인된 evidence 첨부만 `public-attachments/`에 archive한다.
- 전체 백엔드 자동 테스트, Ruff와 formatter 검증을 통과한 상태에서 전달한다.

현재 AWS baseline은 CloudFront → ALB → private ECS Fargate와 private RDS PostgreSQL 연결, 관리자·시민 CloudFront, 공개 첨부 S3까지 배포 확인했다. 최신 image와 정적 build를 배포한 뒤 다시 확인해야 하는 항목:

- profile catalog와 enum 수정 승인까지 포함한 Agent 실행 → 검토 → Publish → 시민 조회 전체 smoke
- 비공개 `review-attachments/` 업로드와 관리자 presigned URL 열기 smoke
- 관리자 mutation API의 운영 인증·접근 제한

새 이미지는 먼저 `/health`로 기동을 확인하고, 이어서 배포 PostgreSQL에서 Agent
실행부터 검토와 Publish까지 같은 이미지로 통합 검증한다. 운영 인증은 현재 MVP
smoke와 분리된 후속 보안 작업이다.

## Docker build context and paths

Docker build context는 저장소 루트를 사용한다.

```text
docker build -f backend/Dockerfile .
```

현재 `backend/app/main.py`의 fixture API는 저장소 루트의
`demo-data/approved-policy.json`을 읽는다. `backend/`만 build context로 사용하면
`demo-data/`가 제외되어 fixture API가 실패한다.

컨테이너 안에서는 다음 배치를 유지한다.

```text
/app/backend   Python application and pyproject.toml
/app/demo-data demo fixture required by the current fallback API
```

실행 working directory는 `/app/backend`로 둔다. 실제 `storage/raw` 수집 데이터,
로컬 SQLite DB, `.env`, test cache와 build output은 이미지에 포함하지 않는다.

## Runtime and dependencies

- Python: 3.11 이상
- Application server: Uvicorn
- Application port: 8000
- Health path: `/health`
- PostgreSQL driver: psycopg 3
- ORM: SQLAlchemy 2
- Crawler: `scrapling[fetchers]`의 정적 Fetcher
- Browser crawler나 Scrapling Spider는 현재 Agent 경로에 추가하지 않는다.

Scrapling 의존성이 컨테이너 build에 포함되므로 Python wheel과 필요한 OS runtime
library 설치가 성공하는지 실제 image build로 확인한다. 브라우저 자동화 binary는
현재 정적 Fetcher 경로의 필수 조건으로 간주하지 않는다.

## Environment variables

다음 값은 이미지에 굽거나 Git에 커밋하지 않고 배포 환경에서 주입한다.

| Variable | Local | AWS deployment |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./gangnam-change-agent.db` | `postgresql+psycopg://...` |
| `OPENAI_API_KEY` | 개발자 로컬 secret | AWS secret 환경변수 |
| `OPENAI_OCR_MODEL` | `.env.example` 기본값 | 필요 시 재정의 |
| `OPENAI_POLICY_MODEL` | `.env.example` 기본값 | 필요 시 재정의 |
| `BACKEND_CORS_ORIGINS` | localhost 시민·관리자 주소 | 배포된 시민 PWA·관리자 HTTPS origin |
| `S3_ATTACHMENT_BUCKET` | 비워 두면 archive 비활성 | 공개 근거 첨부 버킷 이름 |
| `S3_ATTACHMENT_REGION` | `ap-northeast-2` | 버킷 리전 |
| `S3_ATTACHMENT_PREFIX` | `public-attachments` | 공개 첨부 key prefix |
| `PUBLIC_ATTACHMENT_BASE_URL` | 선택 | S3 또는 CloudFront 공개 base URL |
| `S3_REVIEW_ATTACHMENT_PREFIX` | `review-attachments` | 관리자 검토용 비공개 첨부 key prefix |
| `S3_REVIEW_URL_EXPIRES_IN` | `900` | 관리자 presigned URL 만료 시간 |

PostgreSQL 비밀번호, OpenAI key, AWS credential과 내부 접속 주소는 로그, Dockerfile,
image layer, Git 문서에 실제 값으로 남기지 않는다.

백엔드 실행 IAM Role에는 공개·검토 첨부 prefix의 `s3:PutObject`와 검토 prefix의 `s3:GetObject` 권한을 부여한다.
정적 access key는 주입하지 않는다. 시민 PWA가 고정 URL로 접근할 수 있도록 해당 공개
prefix 또는 앞단 CloudFront 읽기 정책을 설정하되 버킷 전체를 공개하지 않는다.

## Database boundary

D-007에 따라 로컬은 SQLite, AWS는 PostgreSQL을 사용하고 같은 SQLAlchemy 모델과
repository를 소비한다.

서버 DB 저장 허용 범위:

- 공개 SourceNotice
- AgentRun과 공개 공고 처리 로그
- PolicyPackage 후보와 승인 상태
- FieldDefinitionProposal과 FieldDefinitionReview

서버 DB 저장 금지 범위:

- 시민 프로필
- 시민별 정책 판정 결과
- 시민의 민감 속성

현재 FastAPI startup은 SQLAlchemy schema를 초기화하며 PostgreSQL dialect DDL
compile까지 검증됐다. PostgreSQL live 연결과 운영 migration 방식은 AWS DB 연결
단계에서 다시 확인한다.

## Container verification

### Admin Codex next action

Dockerfile과 PostgreSQL 실행 환경을 준비한 뒤 아래 검증 목록을 수행하고, 마지막에
`backend/scripts/smoke_agent_review_publish.py`를 격리된 DB에 실행한다. 결과와 실패
지점을 Admin Work log에 기록한 후 원래 관리자 UI·통합 작업으로 복귀한다.

관리자·통합 담당은 최소한 다음을 실제로 확인하고 자신의 Work log에 기록한다.

1. 저장소 루트 context에서 image build 성공
2. secret을 image에 포함하지 않고 container start 성공
3. container 내부 Uvicorn이 `0.0.0.0:8000`에서 listen
4. `/health` HTTP 200과 응답 body 확인
5. 현재 fallback 정책 API가 필요하면 `demo-data` 포함 여부 확인
6. container 종료 후 secret과 시민 데이터가 log에 남지 않았는지 확인
7. Agent API 실행 결과가 DB에 저장되고 AgentRun을 다시 조회할 수 있는지 확인
8. PostgreSQL 연결과 관리자 API가 준비되면 관련 smoke 재실행

격리된 배포 DB에서 전체 API 흐름은 저장소 루트 기준으로 다음 스크립트를 사용한다.
이 스크립트는 실제 AgentRun과 검토·승인 데이터를 생성하므로 운영 DB에는 실행하지
않는다.

```powershell
$env:BACKEND_BASE_URL="https://배포된-백엔드"
$env:SMOKE_NOTICE_URL="https://www.gangnam.go.kr/notice/view.do?id=61922"
$env:SMOKE_ALLOW_MUTATIONS="true"
python backend/scripts/smoke_agent_review_publish.py
```

이전 승인 정책과의 diff까지 확인할 때만 `SMOKE_PREVIOUS_POLICY_ID`를 추가한다. 성공
결과에는 `run_id`, `policy_id`, 승인한 field review 목록과 최종 `approved` 상태가
출력된다.

관리자 승인·반려 endpoint는 데모 통합용 최소 API이며 애플리케이션 자체 인증을 아직
포함하지 않는다. AWS에서 공용 인터넷에 노출하기 전 관리자 경로에 인증 또는 동등한
접근 제한을 적용하고, 시민 PWA에는 승인 정책 GET endpoint만 제공한다.

실행하지 않은 PostgreSQL, OpenAI, AWS 검증을 성공했다고 기록하지 않는다.

## Handoff and update rule

- Agent·백엔드 담당은 실행 명령, 필수 환경변수, API 또는 DB startup 방식이 바뀌면
  이 문서를 갱신한다.
- 관리자·통합 담당은 Dockerfile과 AWS 설정의 실제 결과를
  `docs/worklogs/admin-integration/WORKLOG.md`에 기록한다.
- 배포 중 백엔드 코드 변경이 필요하면 원인을 먼저 Agent·백엔드 담당에게 공유하고
  ownership을 임의로 확장하지 않는다.
