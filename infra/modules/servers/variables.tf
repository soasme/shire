variable "ssh_keys" { type = list(string) }
variable "site_domain" {}
variable "site_region" {}
variable "site_inventory_spec" { type = list(object({
  name = string
  size = string
  image = string
  tags = list(string)
})) }
