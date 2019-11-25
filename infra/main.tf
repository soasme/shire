# Below variables are required for provisioning terraform resources properly.
# The recommended way to setup them is by specifying envvar `TF_VAR_...`,
# such as `TF_VAR_do_token="..."`.

variable "do_token" {}
variable "do_access_key" {}
variable "do_secret_key" {}
variable "do_project_name" {}
variable "do_ssh_keys" { type = "list" }
variable "site_region" {}
variable "site_domain" {}
variable "site_domain_txt" {}
variable "site_domain_mx" { type = "list" }
variable "site_inventory_spec" { type = "list" }

# All digitalocean related resources, outputs will require this provider.
# So, let's claim it first.

provider "digitalocean" {
  token = "${var.do_token}"
  spaces_access_id = "${var.do_access_key}"
  spaces_secret_key = "${var.do_secret_key}"
}

# Provision IP addresses (for lb)

resource "digitalocean_floating_ip" "site_domain_vip" {
  region            = var.site_region
}

# Provision Computational Resources

resource "digitalocean_droplet" "server" {
  count     = length(var.site_inventory_spec)
  name      = format(
    "%s.%s.svr.%s",
    var.site_inventory_spec[count.index]["name"],
    var.site_region,
    var.site_domain
  )
  size      = var.site_inventory_spec[count.index]["size"]
  image     = var.site_inventory_spec[count.index]["image"]
  region    = var.site_region
  tags      = var.site_inventory_spec[count.index]["tags"]
  ssh_keys  = var.do_ssh_keys
  private_networking = true
}

# Note: by default vip 0001 is bound to the load balancer host.
# In the future, we might introduce a secondary load balancer,
# and use a script to attach ip dynamically to fail over.
resource "digitalocean_floating_ip_assignment" "vip" {
  ip_address = "${digitalocean_floating_ip.site_domain_vip.ip_address}"
  droplet_id = "${digitalocean_droplet.server[0].id}"
}

# Provision Site Domain and Name Records

module "dns" {
  source = "./modules/dns"
  site_domain = var.site_domain
  site_domain_txt = var.site_domain_txt
  site_domain_mx = var.site_domain_mx
  site_domain_vip = digitalocean_floating_ip.site_domain_vip.ip_address
}
