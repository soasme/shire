# Below variables are required for provisioning terraform resources properly.
# The recommended way to setup them is by specifying envvar `TF_VAR_...`,
# such as `TF_VAR_do_token="..."`.

variable "do_token" {}
variable "do_access_key" {}
variable "do_secret_key" {}
variable "do_project_name" {}
variable "do_ssh_keys" { type = list(string) }
variable "site_region" {}
variable "site_domain" {}
variable "blog_domain_cname" {}
variable "site_domain_txt" {}
variable "site_domain_mx" { type = list(object({
  priority = number
  value = string
})) }
variable "site_inventory_spec" { type = list(object({
  name = string
  size = string
  image = string
  tags = list(string)
})) }

# All digitalocean related resources, outputs will require this provider.
# So, let's claim it first.

provider "digitalocean" {
  token = var.do_token
  spaces_access_id = var.do_access_key
  spaces_secret_key = var.do_secret_key
}

# Provision IP addresses (for lb)
# Provision Computational Resources

module "servers" {
  source = "./modules/servers"
  ssh_keys = var.do_ssh_keys
  site_region = var.site_region
  site_domain = var.site_domain
  site_inventory_spec = var.site_inventory_spec
}

# Provision Site Domain and Name Records
# TODO: add blog dns.
module "dns" {
  source = "./modules/dns"
  site_domain = var.site_domain
  site_domain_txt = var.site_domain_txt
  site_domain_mx = var.site_domain_mx
  site_domain_vip = module.servers.site_vip
  blog_domain_cname = var.blog_domain_cname
}

