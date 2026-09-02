data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name               = "${var.project_name}-${var.environment}-instance"
  description        = "Role assumed by the Ops Status Board EC2 instance."
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-instance"
    }
  )
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.project_name}-${var.environment}-instance"
  role = aws_iam_role.instance.name

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-instance"
    }
  )
}

data "aws_iam_policy_document" "backup_access" {
  statement {
    sid     = "ListPostgreSQLBackups"
    effect  = "Allow"
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.backups.arn,
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["postgresql/*"]
    }
  }

  statement {
    sid    = "ReadAndWritePostgreSQLBackups"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.backups.arn}/postgresql/*",
    ]
  }

  statement {
    sid    = "UseBackupEncryptionKey"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]
    resources = [
      aws_kms_key.backups.arn,
    ]
  }
}

resource "aws_iam_role_policy" "backup_access" {
  name   = "${var.project_name}-${var.environment}-backup-access"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.backup_access.json
}

data "aws_iam_policy_document" "runtime_parameter_access" {
  statement {
    sid    = "ReadRuntimeParameters"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]
    resources = [
      aws_ssm_parameter.admin_api_token.arn,
      aws_ssm_parameter.database_password.arn,
    ]
  }

  statement {
    sid     = "DecryptRuntimeParameters"
    effect  = "Allow"
    actions = ["kms:Decrypt"]
    resources = [
      aws_kms_key.backups.arn,
    ]
  }
}

resource "aws_iam_role_policy" "runtime_parameter_access" {
  name   = "${var.project_name}-${var.environment}-runtime-parameter-access"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.runtime_parameter_access.json
}

data "aws_iam_policy_document" "cloudwatch_agent" {
  statement {
    sid    = "WriteSelectedNginxLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.nginx_access.arn}:*",
      "${aws_cloudwatch_log_group.nginx_error.arn}:*",
    ]
  }

  statement {
    sid       = "PublishSelectedHostMetrics"
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["CWAgent"]
    }
  }
}

resource "aws_iam_role_policy" "cloudwatch_agent" {
  name   = "${var.project_name}-${var.environment}-cloudwatch-agent"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.cloudwatch_agent.json
}
