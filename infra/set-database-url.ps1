$ErrorActionPreference = "Stop"

$region = terraform output -raw aws_region 2>$null
if (-not $region) {
    $region = "ap-northeast-2"
}

$masterSecretArn = terraform output -raw rds_master_secret_arn
$databaseUrlSecretArn = terraform output -raw database_url_secret_arn
$endpoint = terraform output -raw rds_endpoint
$credentialsJson = aws secretsmanager get-secret-value --region $region --secret-id $masterSecretArn --query SecretString --output text
$credentials = $credentialsJson | ConvertFrom-Json
$username = [Uri]::EscapeDataString($credentials.username)
$password = [Uri]::EscapeDataString($credentials.password)
$databaseUrl = "postgresql+psycopg://${username}:${password}@${endpoint}:5432/gangnam_change_agent"

aws secretsmanager put-secret-value --region $region --secret-id $databaseUrlSecretArn --secret-string $databaseUrl | Out-Null
Write-Host "DATABASE_URL secret updated. Run terraform apply with deploy_service=true."
