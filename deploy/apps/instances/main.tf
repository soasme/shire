provider "digitalocean" {}

data "digitalocean_vpc" "this" {
  id = var.vpc_id
}

data "cloudinit_config" "app" {
  gzip = false
  base64_encode = false

  part {
    content_type = "text/x-shellscript"
    filename = "bootstrap.sh"
    content = <<EOT
      yum update -y \
        && yum install -y ansible \
        && ansible-galaxy install ${join(" ", var.app_ansible_galaxy_requirements)}
    EOT
  }

  part {
    content_type = "text/x-shellscript"
    filename = "init-server.sh"
    content = <<EOT
      /usr/local/bin/ansible-pull -U https://github.com/soasme/shire  \
        -i 127.0.0.1, \
        deploy/apps/instances/app.yml
    EOT
  }
}

resource "digitalocean_droplet" "app" {
  count              = var.app_instances_count

  name               = join("-", [var.app_instances_prefix, format("%04d", count.index)])
  size               = var.app_instances_size
  image              = var.app_instances_image
  tags               = var.app_instances_tags
  user_data          = local.app_user_data
  region             = data.cloudinit_config.app.rendered
  ssh_keys           = var.ssh_keys
  vpc_uuid           = var.vpc_id
  private_networking = true
  monitoring         = true
}

resource "digitalocean_droplet" "db" {
  count              = var.db_instances_count

  name               = join("-", [var.db_instances_prefix, format("%04d", count.index)])
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
  name                    = join("-", [var.db_instances_prefix, format("%04d", count.index)])
  size                    = var.db_volumes_size
  initial_filesystem_type = var.db_volumes_fstype
  description             = "The volume for instance ${digitalocean_droplet.db.name}"
}

resource "digitalocean_volume_attachment" "db" {
  count       = var.db_instances_count

  droplet_id  = digitalocean_droplet.db[count.index].id
  volume_id   = digitalocean_volume.db[count.index].id
}
