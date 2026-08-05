output "aws_region" {
  value = var.aws_region
}

output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.main.address
}

output "rds_master_secret_arn" {
  value     = aws_db_instance.main.master_user_secret[0].secret_arn
  sensitive = true
}

output "database_url_secret_arn" {
  value = aws_secretsmanager_secret.database_url.arn
}

output "backend_url" {
  value = "https://${aws_cloudfront_distribution.backend.domain_name}"
}

output "frontend_urls" {
  value = {
    for name, distribution in aws_cloudfront_distribution.frontend : name => "https://${distribution.domain_name}"
  }
}

output "frontend_bucket_names" {
  value = {
    for name, bucket in aws_s3_bucket.frontend : name => bucket.id
  }
}

output "frontend_distribution_ids" {
  value = {
    for name, distribution in aws_cloudfront_distribution.frontend : name => distribution.id
  }
}

output "public_attachment_url" {
  value = "https://${aws_cloudfront_distribution.public_attachments.domain_name}"
}
