variable "do_token" {}
variable "do_project_name" {}
variable "do_ssh_keys" { type = "list" }

provider "digitalocean" {
  token = "${var.do_token}"
}

resource "digitalocean_droplet" "fun0001" {
  name      = "fun0001"
  size      = "s-1vcpu-1gb"
  image     = "centos-7-x64"
  region    = "sfo2"
  tags      = ["app0001", "bas0001"]
  ssh_keys  = "${var.do_ssh_keys}"
  private_networking = true
}
