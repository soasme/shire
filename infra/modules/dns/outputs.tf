output "site_domain_fqdn" {
  value = "${digitalocean_record.at_A.fqdn}"
}
