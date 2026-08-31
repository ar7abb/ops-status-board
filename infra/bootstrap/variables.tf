variable "aws_region" {
  description = "AWS region for the Ops Status Board environment."
  type        = string
  default     = "eu-north-1"
}

variable "state_bucket_name" {
  description = "Globally unique S3 bucket name used for Terraform remote state."
  type        = string
}