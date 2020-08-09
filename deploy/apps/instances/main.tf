provider "digitalocean" {}

data "digitalocean_vpc" "this" {
  id = var.vpc_id
}

resource "digitalocean_droplet" "app" {
  count              = var.app_instances_count

  name               = join("-", [var.app_instances_prefix, format("%04d", count.index)])
  size               = var.app_instances_size
  image              = var.app_instances_image
  tags               = var.app_instances_tags
  region             = data.digitalocean_vpc.this.region
  ssh_keys           = var.ssh_keys
  private_networking = true
}

resource "digitalocean_droplet" "db" {
  count              = var.db_instances_count

  name               = join("-", [var.db_instances_prefix, format("%04d", count.index)])
  size               = var.db_instances_size
  image              = var.db_instances_image
  tags               = var.db_instances_tags
  region             = data.digitalocean_vpc.this.region
  ssh_keys           = var.ssh_keys
  private_networking = true
}
