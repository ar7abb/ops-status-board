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
