locals {
  runtime_parameter_prefix = "/${var.project_name}/${var.environment}/runtime"
}

resource "random_password" "database" {
  length  = 32
  special = false
}

resource "random_password" "admin_api_token" {
  length  = 48
  special = false
}

resource "aws_ssm_parameter" "database_password" {
  name        = "${local.runtime_parameter_prefix}/database-password"
  description = "Database password for the Ops Status Board workload."
  type        = "SecureString"
  tier        = "Standard"
  key_id      = aws_kms_key.backups.arn
  value       = random_password.database.result

  tags = merge(
    local.common_tags,
    {
      Name    = "${var.project_name}-${var.environment}-database-password"
      Purpose = "application-runtime"
    }
  )
}

resource "aws_ssm_parameter" "admin_api_token" {
  name        = "${local.runtime_parameter_prefix}/admin-api-token"
  description = "Administrative API token for the Ops Status Board workload."
  type        = "SecureString"
  tier        = "Standard"
  key_id      = aws_kms_key.backups.arn
  value       = random_password.admin_api_token.result

  tags = merge(
    local.common_tags,
    {
      Name    = "${var.project_name}-${var.environment}-admin-api-token"
      Purpose = "application-runtime"
    }
  )
}

resource "aws_s3_bucket" "ansible_transfer" {
  bucket_prefix = "${var.project_name}-${var.environment}-ssm-"
  force_destroy = true

  tags = merge(
    local.common_tags,
    {
      Name    = "${var.project_name}-${var.environment}-ansible-transfer"
      Purpose = "ansible-ssm-temporary-transfer"
    }
  )
}

resource "aws_s3_bucket_ownership_controls" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.backups.arn
      sse_algorithm     = "aws:kms"
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  rule {
    id     = "expire-temporary-ansible-transfers"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

data "aws_iam_policy_document" "ansible_transfer_require_tls" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.ansible_transfer.arn,
      "${aws_s3_bucket.ansible_transfer.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "ansible_transfer_require_tls" {
  bucket = aws_s3_bucket.ansible_transfer.id
  policy = data.aws_iam_policy_document.ansible_transfer_require_tls.json

  depends_on = [aws_s3_bucket_public_access_block.ansible_transfer]
}
