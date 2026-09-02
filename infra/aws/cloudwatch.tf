locals {
  cloudwatch_namespace = "${var.project_name}/${var.environment}"
}

resource "aws_cloudwatch_log_group" "nginx_access" {
  name              = "/${var.project_name}/${var.environment}/nginx/access"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-${var.environment}-nginx-access"
    Purpose = "structured-http-access-logs"
  })
}

resource "aws_cloudwatch_log_group" "nginx_error" {
  name              = "/${var.project_name}/${var.environment}/nginx/error"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = merge(local.common_tags, {
    Name    = "${var.project_name}-${var.environment}-nginx-error"
    Purpose = "nginx-error-logs"
  })
}

resource "aws_cloudwatch_log_metric_filter" "http_5xx" {
  name           = "${var.project_name}-${var.environment}-http-5xx"
  pattern        = "{ $.status >= 500 }"
  log_group_name = aws_cloudwatch_log_group.nginx_access.name

  metric_transformation {
    name          = "Http5xxCount"
    namespace     = local.cloudwatch_namespace
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "root_disk_used" {
  alarm_name          = "${var.project_name}-${var.environment}-root-disk-high"
  alarm_description   = "Root filesystem usage stayed above the approved threshold for ten minutes."
  namespace           = "CWAgent"
  metric_name         = "disk_used_percent"
  statistic           = "Average"
  period              = var.cloudwatch_metrics_interval_seconds
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.disk_used_alarm_threshold_percent
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "missing"

  dimensions = {
    InstanceId = aws_instance.app.id
    path       = "/"
    fstype     = "ext4"
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "memory_available" {
  alarm_name          = "${var.project_name}-${var.environment}-memory-low"
  alarm_description   = "Available memory stayed below the approved threshold for ten minutes."
  namespace           = "CWAgent"
  metric_name         = "mem_available_percent"
  statistic           = "Average"
  period              = var.cloudwatch_metrics_interval_seconds
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.memory_available_alarm_threshold_percent
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "missing"

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "instance_status" {
  alarm_name          = "${var.project_name}-${var.environment}-instance-status-failed"
  alarm_description   = "The EC2 instance failed its combined status check twice."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "missing"

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "http_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-http-5xx"
  alarm_description   = "Nginx recorded repeated server errors during one five-minute period."
  namespace           = local.cloudwatch_namespace
  metric_name         = "Http5xxCount"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = var.http_5xx_alarm_threshold
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = local.common_tags
}
