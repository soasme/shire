provider "digitalocean" {}

resource "digitalocean_vpc" "this" {
  name     = var.name
  ip_range = var.ip_range
  region   = var.region
}
