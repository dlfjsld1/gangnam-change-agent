variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-northeast-2"
}

variable "project_name" {
  description = "Prefix for resource names."
  type        = string
  default     = "gangnam-change-agent"
}

variable "image_tag" {
  description = "ECR image tag deployed to App Runner."
  type        = string
  default     = "latest"
}

variable "deploy_service" {
  description = "Create App Runner after the DATABASE_URL secret has a value and the image exists."
  type        = bool
  default     = false
}

variable "backend_cors_origins" {
  description = "Comma-separated deployed frontend origins."
  type        = string
  default     = ""
}
