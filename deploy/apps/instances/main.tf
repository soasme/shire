resource "digitalocean_droplet" "app" {
  count              = var.app_instances_count
  name               = join("-", [var.app_instances_prefix, format("%04d", count.index)])
  size               = var.app_size
  image              = var.app_image
  tags               = ["app"]
  region             = var.region
  ssh_keys           = var.ssh_keys
  private_networking = true
}

resource "digitalocean_droplet" "db" {
  count              = var.db_instances_count
  name               = join("-", [var.db_instances_prefix, format("%04d", count.index)])
  size               = var.db_size
  image              = var.db_image
  tags               = ["db"]
  region             = var.region
  ssh_keys           = var.ssh_keys
  private_networking = true
}
