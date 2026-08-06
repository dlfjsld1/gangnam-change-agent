resource "aws_s3_bucket" "public_attachments" {
  bucket = "${var.project_name}-public-attachments-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "public_attachments" {
  bucket                  = aws_s3_bucket.public_attachments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "public_attachments" {
  name                              = "${var.project_name}-public-attachments"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "public_attachments" {
  enabled = true
  origin {
    domain_name              = aws_s3_bucket.public_attachments.bucket_regional_domain_name
    origin_id                = "public-attachments-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.public_attachments.id
  }
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "public-attachments-s3"
    viewer_protocol_policy = "redirect-to-https"
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}

data "aws_iam_policy_document" "public_attachments_read" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.public_attachments.arn}/public-attachments/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.public_attachments.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "public_attachments" {
  bucket = aws_s3_bucket.public_attachments.id
  policy = data.aws_iam_policy_document.public_attachments_read.json
}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

data "aws_iam_policy_document" "ecs_public_attachments" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.public_attachments.arn}/public-attachments/*"]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.public_attachments.arn}/review-attachments/*"]
  }
}

resource "aws_iam_role_policy" "ecs_public_attachments" {
  name   = "write-public-attachments"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_public_attachments.json
}
