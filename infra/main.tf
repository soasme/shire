variable "do_token" {}
variable "do_project_name" {}
variable "do_ssh_keys" { type = "list" }

provider "digitalocean" {
  token = "${var.do_token}"
}

resource "digitalocean_droplet" "server_0001" {
  name      = "0001.sfo2.svc.marksth.fun"
  size      = "s-1vcpu-1gb"
  image     = "centos-7-x64"
  region    = "sfo2"
  tags      = ["lb0001", "web0001", "db0001", "worker0001", "lb", "web", "db", "worker"]
  ssh_keys  = "${var.do_ssh_keys}"
  private_networking = true
}

output "server_00001_ipv4_address" {
  value = digitalocean_droplet.server_0001.ipv4_address
}
