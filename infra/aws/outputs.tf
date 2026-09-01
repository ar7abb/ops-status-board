output "instance_id" {
  description = "ID of the Ops Status Board EC2 instance."
  value       = aws_instance.app.id
}

output "backup_bucket_name" {
  description = "Name of the private PostgreSQL backup bucket."
  value       = aws_s3_bucket.backups.id
}
