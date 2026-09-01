variable "aws_region" {
  description = "AWS region for the Ops Status Board environment."
  type        = string
  default     = "eu-north-1"
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
