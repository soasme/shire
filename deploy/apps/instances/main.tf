provider "digitalocean" {}

data "digitalocean_vpc" "this" {
  id = var.vpc_id
}

data "cloudinit_config" "app" {
  gzip          = false
  base64_encode = false

  part {
    filename = "init-config.cfg"
    content_type = "text/cloud-config"
    content = yamlencode({
      write_files = [
        {
          encoding    = "b64"
          content     = base64encode(join("\n", [
            for k, v in var.app_instances_config:
            "${upper(k)}=${v}"
          ]))
          owner       = "root:root"
          path        = "/etc/shire/shire.conf"
          permissions = "0640"
        }
      ]
    })
  }
}

resource "digitalocean_droplet" "app" {
  count              = var.app_instances_count

  name               = join("-", [var.app_instances_prefix, format("%04d", count.index+1)])
  size               = var.app_instances_size
  image              = var.app_instances_image
  tags               = var.app_instances_tags
  region             = data.digitalocean_vpc.this.region
  user_data          = data.cloudinit_config.app.rendered
  ssh_keys           = var.ssh_keys
  vpc_uuid           = var.vpc_id
  private_networking = true
  monitoring         = true
}

resource "digitalocean_droplet" "db" {
  count              = var.db_instances_count

  name               = join("-", [var.db_instances_prefix, format("%04d", count.index+1)])
  size               = var.db_instances_size
  image              = var.db_instances_image
  tags               = var.db_instances_tags
  region             = data.digitalocean_vpc.this.region
  ssh_keys           = var.ssh_keys
  vpc_uuid           = var.vpc_id
  private_networking = true
  monitoring         = true
}

resource "digitalocean_volume" "db" {
  count                   = var.db_instances_count

  region                  = data.digitalocean_vpc.this.region
  name                    = join("-", [var.db_instances_prefix, format("%04d", count.index+1)])
  size                    = var.db_volumes_size
  initial_filesystem_type = "ext4"
  description             = "The volume for instance ${digitalocean_droplet.db[count.index].name}"
}

resource "digitalocean_volume_attachment" "db" {
  count       = var.db_instances_count

  droplet_id  = digitalocean_droplet.db[count.index].id
  volume_id   = digitalocean_volume.db[count.index].id
}
