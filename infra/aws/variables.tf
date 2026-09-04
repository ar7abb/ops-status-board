variable "aws_region" {
  description = "AWS region for the Ops Status Board environment."
  type        = string
  default     = "eu-north-1"
}

variable "ubuntu_ami_id" {
  description = "Reviewed Ubuntu 24.04 x86_64 AMI ID for the workload Region. Pin this value so unrelated applies cannot replace EC2 when a newer image appears."
  type        = string

  validation {
    condition     = can(regex("^ami-[0-9a-f]+$", var.ubuntu_ami_id))
    error_message = "ubuntu_ami_id must be a valid EC2 AMI ID beginning with ami-."
  }
}

variable "project_name" {
  description = "Stable project name used for resource names and tags."
  type        = string
  default     = "ops-status-board"
}

variable "environment" {
  description = "Deployment environment represented by these resources."
  type        = string
  default     = "lab"
}

variable "github_oidc_subject" {
  description = "Exact private GitHub OIDC subject for the approved repository and production environment."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^repo:[^:]+/[^:]+:environment:[^:]+$", var.github_oidc_subject))
    error_message = "github_oidc_subject must identify one exact repository and environment."
  }
}

variable "vpc_cidr" {
  description = "Private IPv4 address range assigned to the project VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Private IPv4 address range assigned to the public subnet."
  type        = string
  default     = "10.20.1.0/24"
}

variable "availability_zone" {
  description = "Availability Zone that contains the public subnet."
  type        = string
  default     = "eu-north-1a"
}

variable "instance_type" {
  description = "EC2 instance type used by the cost-controlled lab workload."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size_gib" {
  description = "Size in GiB of the encrypted EC2 root EBS volume."
  type        = number
  default     = 25

  validation {
    condition     = var.root_volume_size_gib >= 8 && var.root_volume_size_gib <= 100
    error_message = "The root volume size must be between 8 and 100 GiB."
  }
}

variable "backup_retention_days" {
  description = "Days to retain current PostgreSQL backup objects before expiration."
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 90
    error_message = "Backup retention must be between 7 and 90 days."
  }
}

variable "cloudwatch_log_retention_days" {
  description = "Days to retain the selected Nginx logs in CloudWatch Logs."
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30], var.cloudwatch_log_retention_days)
    error_message = "CloudWatch log retention must use an approved short retention period."
  }
}

variable "cloudwatch_metrics_interval_seconds" {
  description = "Collection interval for the two CloudWatch Agent host metrics."
  type        = number
  default     = 300

  validation {
    condition     = var.cloudwatch_metrics_interval_seconds >= 60
    error_message = "CloudWatch Agent metrics must not use high-resolution collection below 60 seconds."
  }
}

variable "disk_used_alarm_threshold_percent" {
  description = "Root filesystem usage percentage that triggers the disk alarm."
  type        = number
  default     = 85

  validation {
    condition     = var.disk_used_alarm_threshold_percent >= 70 && var.disk_used_alarm_threshold_percent <= 95
    error_message = "The disk alarm threshold must be between 70 and 95 percent."
  }
}

variable "memory_available_alarm_threshold_percent" {
  description = "Available memory percentage below which the memory alarm triggers."
  type        = number
  default     = 10

  validation {
    condition     = var.memory_available_alarm_threshold_percent >= 5 && var.memory_available_alarm_threshold_percent <= 30
    error_message = "The available-memory alarm threshold must be between 5 and 30 percent."
  }
}

variable "http_5xx_alarm_threshold" {
  description = "Five-minute HTTP 5xx count that triggers the application alarm."
  type        = number
  default     = 3

  validation {
    condition     = var.http_5xx_alarm_threshold >= 1 && var.http_5xx_alarm_threshold <= 20
    error_message = "The HTTP 5xx alarm threshold must be between 1 and 20 responses."
  }
}
