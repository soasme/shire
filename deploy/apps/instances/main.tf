provider "digitalocean" {}

data "digitalocean_vpc" "this" {
  id = var.vpc_id
}

locals {
  ansible_pull="ansible-galaxy install ${join(" ", var.app_ansible_galaxy_requirements)}; ANSIBLE_PYTHON_INTERPRETER=/usr/bin/python3 /usr/local/bin/ansible-pull -U https://github.com/soasme/shire -i 127.0.0.1, deploy/apps/instances/app.yml 2>&1 > /var/log/ansible-pull.log"
}

resource "digitalocean_droplet" "app" {
  count              = var.app_instances_count

  name               = join("-", [var.app_instances_prefix, format("%04d", count.index+1)])
  size               = var.app_instances_size
  image              = var.app_instances_image
  tags               = var.app_instances_tags
  region             = data.digitalocean_vpc.this.region
  ssh_keys           = var.ssh_keys
  vpc_uuid           = var.vpc_id
  private_networking = true
  monitoring         = true

  provisioner "remote-exec" {
    connection {
      type     = "ssh"
      user     = "root"
      host     = self.ipv4_address
    }
    inline = [
      "yum update -y",
      "yum install -y python3 git",
      "python3 -mpip install -U pip ansible",
      local.ansible_pull,
      "echo */30 * * * * ${local.ansible_pull} | crontab",
    ]
  }
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
