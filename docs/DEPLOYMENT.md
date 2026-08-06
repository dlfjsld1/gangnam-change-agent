# AWS 배포 가이드

## 현재 구성

- 리전: ap-northeast-2 (서울)
- 실행: Amazon ECS Fargate
- 공개 경로: CloudFront HTTPS → public ALB HTTP → private ECS task
- 데이터베이스: private Amazon RDS for PostgreSQL 16
- 이미지: Amazon ECR
- 비밀정보: Secrets Manager의 DATABASE_URL
- 외부 공고 접근: private subnet → NAT Gateway
- 공개 근거 첨부: 비공개 S3 `public-attachments/` → CloudFront HTTPS

App Runner는 서울 리전을 지원하지 않으므로 사용하지 않는다.

## 현재 backend URL

https://d25409t9vvq1vj.cloudfront.net

현재 배포 baseline은 health, 관리자 조회 API, 승인 정책 조회와 CORS를 확인했다. 최신 profile catalog, enum 수정 승인과 비공개 검토 첨부 변경은 main 병합 후 Backend image·Admin build를 갱신하고 전체 smoke를 다시 수행한다.

## 공개 근거 첨부 URL

https://dpjy1ffhia6ml.cloudfront.net

## 배포 확인

    $backendUrl = terraform -chdir=infra output -raw backend_url
    Invoke-RestMethod "$backendUrl/health"
    Invoke-RestMethod "$backendUrl/api/policy-packages"
    Invoke-RestMethod "$backendUrl/api/profile-fields"
    Invoke-RestMethod "$backendUrl/api/field-definition-reviews"
    aws logs tail /ecs/gangnam-change-agent-backend --region ap-northeast-2 --since 15m
    terraform -chdir=infra plan -detailed-exitcode

정상 기준은 health HTTP 200, ECS desired/running 1/1, ALB target healthy, Terraform No changes다.

## 비용 중지

    terraform -chdir=infra destroy

RDS, NAT Gateway, ALB, CloudFront, ECS는 실행 중 비용이 발생한다. destroy 전에 필요한 데이터 보존 여부를 확인한다.

## 프론트엔드 배포

- 관리자: https://d25mh7hdavvr2k.cloudfront.net
- 시민 PWA: https://d30pysa0iyz6g5.cloudfront.net
- Origin: 비공개 S3 bucket
- 공개 경로: CloudFront HTTPS → S3 OAC
- 두 프론트 origin은 ECS의 `BACKEND_CORS_ORIGINS`에 Terraform으로 자동 반영한다.

재배포:

```powershell
npm.cmd --prefix frontend/admin run build
npm.cmd --prefix frontend/citizen run build
aws s3 sync frontend/admin/dist/ s3://$(terraform -chdir=infra output -json frontend_bucket_names | ConvertFrom-Json | Select-Object -ExpandProperty admin)/ --delete
aws s3 sync frontend/citizen/dist/ s3://$(terraform -chdir=infra output -json frontend_bucket_names | ConvertFrom-Json | Select-Object -ExpandProperty citizen)/ --delete
```

업로드 후 `frontend_distribution_ids` 출력값으로 CloudFront invalidation을 실행한다.
