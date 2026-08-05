# AWS 배포 가이드

## 구성

- 로컬 DB: SQLite (DATABASE_URL 미설정 시 sqlite:///./gangnam-change-agent.db)
- AWS DB: 비공개 Amazon RDS for PostgreSQL
- ORM/마이그레이션: SQLAlchemy 2 / Alembic
- 런타임: ECR 이미지 → App Runner → VPC Connector → RDS
- 비밀정보: App Runner가 Secrets Manager의 DATABASE_URL을 런타임에 참조
- 외부 공고 접근: private subnet → 단일 NAT Gateway

Terraform은 DB 비밀번호나 DATABASE_URL 값을 state에 저장하지 않는다. RDS가 master password를 관리하고, set-database-url.ps1가 AWS API로 읽어 별도 secret에 직접 저장한다.

## 배포 담당자가 준비할 것

1. AWS 계정과 ap-northeast-2 리전에 리소스를 만들 권한을 준비한다.
2. 로컬에 AWS CLI, Docker, Terraform 1.6 이상을 설치한다.
3. aws sts get-caller-identity로 사용할 계정을 확인한다.
4. 관리자 웹과 시민 PWA의 실제 HTTPS origin을 팀원에게 받는다.
5. 예상 비용을 확인한다. RDS, NAT Gateway, App Runner, Secrets Manager는 실행 중 과금된다.
6. infra/terraform.tfvars.example을 infra/terraform.tfvars로 복사하고 CORS origin을 채운다. 이 파일은 커밋하지 않는다.

필요 IAM 범위: VPC/EC2 networking, RDS, Secrets Manager, ECR, App Runner, IAM role/policy 생성 및 PassRole. 가능하면 해커톤 전용 AWS 계정 또는 권한 경계를 사용한다.

## 1차 인프라 생성

    terraform -chdir=infra init
    terraform -chdir=infra plan -out=tfplan
    terraform -chdir=infra apply tfplan

기본 deploy_service=false이므로 VPC, NAT, RDS, ECR, IAM, VPC Connector, secret container까지만 생성된다.

## Backend 이미지 푸시

    $repository = terraform -chdir=infra output -raw ecr_repository_url
    $registry = $repository.Split("/")[0]
    aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin $registry
    docker build -t gangnam-change-agent-backend -f backend/Dockerfile .
    docker tag gangnam-change-agent-backend:latest "$($repository):latest"
    docker push "$($repository):latest"

## DATABASE_URL secret 채우기

    Push-Location infra
    ./set-database-url.ps1
    Pop-Location

스크립트는 RDS가 관리하는 비밀번호를 읽어 URL 인코딩한 뒤 PostgreSQL SQLAlchemy URL로 저장한다. 터미널에 비밀번호나 완성된 URL을 출력하지 않는다.

## 2차 App Runner 생성

infra/terraform.tfvars에서 deploy_service = true, image_tag = "latest"로 바꾼 뒤 실행한다.

    terraform -chdir=infra plan -out=tfplan
    terraform -chdir=infra apply tfplan
    terraform -chdir=infra output -raw app_runner_url

## 배포 확인

    $backendUrl = terraform -chdir=infra output -raw app_runner_url
    Invoke-RestMethod "$backendUrl/health"
    Invoke-RestMethod "$backendUrl/api/policy-packages"
    Invoke-RestMethod "$backendUrl/api/field-definition-reviews"

App Runner 로그에서 Alembic upgrade head 완료를 확인한다. 관리자 승인 후 새 요청 또는 재시작 뒤에도 상태가 유지되는지 확인한다. 시민 프로필이나 매칭 결과가 API 요청, 로그, RDS에 없는지 확인한다.

## 팀원에게 요청할 일

### Agent·Backend 담당

- 이 브랜치의 backend SQLAlchemy/Alembic 변경을 리뷰하고 자신의 브랜치와 합의해 병합한다.
- 새 스키마 변경은 반드시 새 Alembic revision으로 추가한다.
- PostgreSQL DATABASE_URL로 alembic upgrade head와 API smoke test를 실행한다.
- Agent 실행 로그와 공개 정책 저장을 현재 app_state JSON 테이블에서 별도 테이블로 확장할 필요가 있는지 데모 후 결정한다.
- 시민 프로필 데이터가 DB나 서버 로그에 저장되지 않는지 확인한다.

### Admin·Integration 담당

- Terraform plan의 계정, 리전, 예상 리소스와 비용을 검토한다.
- 2단계 apply, ECR push, secret 주입, App Runner smoke test를 수행한다.
- App Runner URL을 두 frontend의 VITE_API_BASE_URL 빌드 값으로 전달한다.
- 배포 후 CORS, HTTPS, /health, CloudWatch 로그를 확인한다.

### Citizen PWA 담당

- 배포된 Backend URL로 production build를 만든다.
- 프로필이 IndexedDB에만 남고 API payload/query/log에 포함되지 않는지 Network 탭으로 확인한다.
- 승인된 정책 조회와 demo fixture fallback을 각각 확인한다.
- 배포한 시민 PWA HTTPS origin을 Admin·Integration 담당에게 전달한다.

### Admin frontend 담당

- 배포된 Backend URL로 production build를 만든다.
- 승인·수정·반려와 AgentRun 조회를 실제 App Runner API로 smoke test한다.
- 배포한 관리자 HTTPS origin을 Admin·Integration 담당에게 전달한다.

## 장애 시 확인 순서

1. App Runner 로그에서 Alembic 또는 DATABASE_URL 오류 확인
2. App Runner instance role의 secretsmanager:GetSecretValue 확인
3. VPC Connector와 App Runner security group 확인
4. RDS security group이 App Runner security group의 5432만 허용하는지 확인
5. secret을 수정했다면 App Runner deployment를 다시 시작
6. 네트워크 장애 데모에는 기존 frontend fixture fallback 사용

## 삭제

비용을 멈추려면 먼저 보존할 데이터와 스크린샷을 확인한 후 실행한다.

    terraform -chdir=infra destroy
