resource "aws_kms_key" "backups" {
  description             = "Encrypts Ops Status Board PostgreSQL backups."
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(
    local.common_tags,
    {
      Name    = "${var.project_name}-${var.environment}-backups"
      Purpose = "postgresql-backups"
    }
  )
}

resource "aws_kms_alias" "backups" {
  name          = "alias/${var.project_name}-${var.environment}-backups"
  target_key_id = aws_kms_key.backups.key_id
}

resource "aws_s3_bucket" "backups" {
  bucket_prefix = "${var.project_name}-${var.environment}-backups-"
  # M11-T04 is the final evidence-preserving teardown. Sanitized recovery proof
  # is published at v0.9; encrypted object versions must now be removed with
  # this project-owned bucket so no chargeable workload storage remains.
  force_destroy = true

  tags = merge(
    local.common_tags,
    {
      Name    = "${var.project_name}-${var.environment}-backups"
      Purpose = "postgresql-backups"
    }
  )

}

resource "aws_s3_bucket_ownership_controls" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.backups.arn
      sse_algorithm     = "aws:kms"
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "short-backup-retention"
    status = "Enabled"

    filter {
      prefix = "postgresql/"
    }

    expiration {
      days = var.backup_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.backups]
}

data "aws_iam_policy_document" "backup_require_tls" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.backups.arn,
      "${aws_s3_bucket.backups.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "backup_require_tls" {
  bucket = aws_s3_bucket.backups.id
  policy = data.aws_iam_policy_document.backup_require_tls.json

  depends_on = [aws_s3_bucket_public_access_block.backups]
}
