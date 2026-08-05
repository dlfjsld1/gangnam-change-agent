# AWS 배포 가이드

## 현재 구성

- 리전: ap-northeast-2 (서울)
- 실행: Amazon ECS Fargate
- 공개 경로: CloudFront HTTPS → public ALB HTTP → private ECS task
- 데이터베이스: private Amazon RDS for PostgreSQL 16
- 이미지: Amazon ECR
- 비밀정보: Secrets Manager의 DATABASE_URL
- 외부 공고 접근: private subnet → NAT Gateway

App Runner는 서울 리전을 지원하지 않으므로 사용하지 않는다.

## 현재 backend URL

https://d25409t9vvq1vj.cloudfront.net

## 배포 확인

    $backendUrl = terraform -chdir=infra output -raw backend_url
    Invoke-RestMethod "$backendUrl/health"
    Invoke-RestMethod "$backendUrl/api/policy-packages"
    Invoke-RestMethod "$backendUrl/api/field-definition-reviews"
    aws logs tail /ecs/gangnam-change-agent-backend --region ap-northeast-2 --since 15m
    terraform -chdir=infra plan -detailed-exitcode

정상 기준은 health HTTP 200, ECS desired/running 1/1, ALB target healthy, Terraform No changes다.

## 비용 중지

    terraform -chdir=infra destroy

RDS, NAT Gateway, ALB, CloudFront, ECS는 실행 중 비용이 발생한다. destroy 전에 필요한 데이터 보존 여부를 확인한다.
