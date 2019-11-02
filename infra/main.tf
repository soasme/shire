# Below variables are required for provisioning terraform resources properly.
# The recommended way to setup them is by specifying envvar `TF_VAR_...`,
# such as `TF_VAR_do_token="..."`.

variable "do_token" {}
variable "do_access_key" {}
variable "do_secret_key" {}
variable "do_project_name" {}
variable "do_ssh_keys" { type = "list" }
variable "site_domain" {}
variable "bucket_name" {}
variable "site_domain_txt" {}
variable "site_domain_mx" { type = "list" }

# All digitalocean related resources, outputs will require this provider.
# So, let's claim it first.

provider "digitalocean" {
  token = "${var.do_token}"
  spaces_access_id = "${var.do_access_key}"
  spaces_secret_key = "${var.do_secret_key}"
}

# Provision Computational Resources

resource "digitalocean_droplet" "server_0001" {
  name      = "0001.sfo2.svr.${var.site_domain}"
  size      = "s-1vcpu-1gb"
  image     = "centos-7-x64"
  region    = "sfo2"
  tags      = ["lb", "web", "db", "mq", "worker", "prom", "dns", ]
  ssh_keys  = "${var.do_ssh_keys}"
  private_networking = true
}

output "server_00001_ipv4_address" {
  value = digitalocean_droplet.server_0001.ipv4_address
}

# Provision Space

resource "digitalocean_spaces_bucket" "bucket" {
  name = var.bucket_name
  region = "sfo2"
}

# Provision IP addresses (for lb)

resource "digitalocean_floating_ip" "vip_0001" {
  region            = "sfo2"
}

# Note: by default vip 0001 is bound to the load blancer host.
# In the future, we might introduce a secondary load balancer,
# and use a script to attach ip dynamically to fail over.
resource "digitalocean_floating_ip_assignment" "vip_0001" {
  ip_address = "${digitalocean_floating_ip.vip_0001.ip_address}"
  droplet_id = "${digitalocean_droplet.server_0001.id}"
}

# Provision Site Domain and Name Records

resource "digitalocean_domain" "site_domain" {
  name      = "${var.site_domain}"
}

resource "digitalocean_record" "at_A" {
  domain    = "${digitalocean_domain.site_domain.name}"
  type      = "A"
  name      = "@"
  ttl       = 300 # 5m
  value     = "${digitalocean_floating_ip.vip_0001.ip_address}"
}

resource "digitalocean_record" "at_txt" {
  domain    = "${digitalocean_domain.site_domain.name}"
  type      = "TXT"
  name      = "@"
  ttl       = 300 # 5m
  value     = "${var.site_domain_txt}"
}

resource "digitalocean_record" "at_mx" {
  count     = "${length(var.site_domain_mx)}"
  domain    = "${digitalocean_domain.site_domain.name}"
  type      = "MX"
  name      = "@"
  ttl       = 3600 # 1h
  priority  = var.site_domain_mx[count.index]["priority"]
  value     = var.site_domain_mx[count.index]["value"]
}

output "site_domain_fqdn" {
  value = "${digitalocean_record.at_A.fqdn}"
}
