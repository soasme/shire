output "site_vip" {
  value = digitalocean_floating_ip.site_domain_vip.ip_address
}
