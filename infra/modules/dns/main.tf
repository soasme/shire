resource "digitalocean_domain" "site_domain" {
  name      = var.site_domain
}

resource "digitalocean_record" "at_A" {
  domain    = digitalocean_domain.site_domain.name
  type      = "A"
  name      = "@"
  ttl       = 300 # 5m
  value     = var.site_domain_vip
}

resource "digitalocean_record" "at_txt" {
  domain    = digitalocean_domain.site_domain.name
  type      = "TXT"
  name      = "@"
  ttl       = 300 # 5m
  value     = var.site_domain_txt
}

resource "digitalocean_record" "at_mx" {
  count     = length(var.site_domain_mx)
  domain    = digitalocean_domain.site_domain.name
  type      = "MX"
  name      = "@"
  ttl       = 3600 # 1h
  priority  = var.site_domain_mx[count.index]["priority"]
  value     = var.site_domain_mx[count.index]["value"]
}

resource "digitalocean_record" "blog_cname" {
  domain    = digitalocean_domain.site_domain.name
  type      = "CNAME"
  name      = "blog"
  ttl       = 300 # 5m
  value     = var.blog_domain_cname
}
