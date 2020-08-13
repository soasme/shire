resource "digitalocean_floating_ip" "site_domain_vip" {
  region            = var.site_region
}

resource "digitalocean_volume" "db" {
  region                  = var.site_region
  name                    = "db"
  size                    = var.db_volume_size
  initial_filesystem_type = "ext4"
  description             = "Persist database data"
}

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
  tags      = var.site_inventory_spec[count.index]["tags"]
  region    = var.site_region
  ssh_keys  = var.ssh_keys
  private_networking = true
}

# Note: by default vip 0001 is bound to the load balancer host.
# In the future, we might introduce a secondary load balancer,
# and use a script to attach ip dynamically to fail over.
resource "digitalocean_floating_ip_assignment" "vip" {
  ip_address = digitalocean_floating_ip.site_domain_vip.ip_address
  droplet_id = digitalocean_droplet.server[0].id
}

resource "digitalocean_volume_attachment" "db" {
  droplet_id = digitalocean_droplet.server[0].id
  volume_id  = digitalocean_volume.db.id
}
