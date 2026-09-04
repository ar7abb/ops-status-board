output "instance_id" {
  description = "ID of the Ops Status Board EC2 instance."
  value       = aws_instance.app.id
}

output "backup_bucket_name" {
  description = "Name of the private PostgreSQL backup bucket."
  value       = aws_s3_bucket.backups.id
}

output "ansible_transfer_bucket_name" {
  description = "Name of the private, non-versioned bucket used for temporary Ansible-over-SSM transfers."
  value       = aws_s3_bucket.ansible_transfer.id
}

output "runtime_parameter_prefix" {
  description = "Parameter Store path containing encrypted application runtime values."
  value       = local.runtime_parameter_prefix
}

output "cloudwatch_access_log_group_name" {
  description = "CloudWatch Logs group that stores structured Nginx access events."
  value       = aws_cloudwatch_log_group.nginx_access.name
}

output "cloudwatch_error_log_group_name" {
  description = "CloudWatch Logs group that stores Nginx error events."
  value       = aws_cloudwatch_log_group.nginx_error.name
}

output "github_actions_deploy_role_arn" {
  description = "ARN stored as the non-secret AWS_DEPLOY_ROLE_ARN GitHub environment variable."
  value       = aws_iam_role.github_actions_deploy.arn
}
