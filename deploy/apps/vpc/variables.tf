variable "name" {
  type        = string
  default     = null
  description = "The name of the VPC."
}

variable "ip_range" {
  type        = string
  default     = "10.0.0.0/24"
  description = "The CIDR of the VPC."
}

variable "region" {
  type        = string
  default     = "sfo2"
  description = "The region of the VPC."
}
