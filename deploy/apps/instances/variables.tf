variable "vpc_id" {
  type        = string
  default     = null
  description = "The id of digitalocean VPC."
}

variable "app_instances_config" {
  type          = map
  default       = {}
  description   = "A of files to write in bootstrap step."
}

variable "app_instances_count" {
  type        = number
  default     = 0
  description = "The total number of instances tagged by app."
}

variable "app_instances_prefix" {
  type        = string
  default     = "app"
  description = "The name prefix of app instances."
}

variable "app_instances_size" {
  type        = string
  default     = "s-1vcpu-1gb"
  description = "The size of app instances."
}

variable "app_instances_image" {
  type        = string
  default     = "centos-7-x64"
  description = "The image of app instances."
}

variable "app_instances_tags" {
  type        = list(string)
  default     = ["app"]
  description = "The tags of app instances."
}

variable "ssh_keys" {
  type        = list(string)
  default     = null
  description = "The list of fingerprints of ssh public keys."
}

variable "db_instances_count" {
  type        = number
  default     = 0
  description = "The total number of instances tagged by db."
}

variable "db_instances_prefix" {
  type        = string
  default     = "db"
  description = "The name prefix of db instances."
}

variable "db_instances_size" {
  type        = string
  default     = "s-1vcpu-1gb"
  description = "The size of db instances."
}

variable "db_instances_image" {
  type        = string
  default     = "centos-7-x64"
  description = "The image of db instances."
}

variable "db_instances_tags" {
  type        = list(string)
  default     = ["db"]
  description = "The tags of db instances."
}

variable "db_volumes_size" {
  type        = number
  default     = 125
  description = "The size of db volumes."
}
