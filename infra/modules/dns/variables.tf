variable "site_domain" {}
variable "site_domain_txt" {}
variable "site_domain_mx" { type = list(object({
  priority = number
  value = string
})) }
variable "site_domain_vip" {}
variable "blog_domain_cname" {}
variable "mail_domain_name" {}
variable "mail_domain_cname" {
  type = list(object({
    name = string
    value = string
  }))
}
