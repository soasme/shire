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

resource "digitalocean_record" "mail_cname" {
  count     = length(var.mail_domain_cname)
  domain    = digitalocean_domain.site_domain.name
  type      = "CNAME"
  name      = var.mail_domain_cname[count.index]["name"]
  value     = var.mail_domain_cname[count.index]["value"]
}

resource "mailgun_domain" "mailer" {
  name          = var.mail_domain_name
  region        = "us"
  spam_action   = "disabled"
}

resource "digitalocean_record" "receive_email" {
  count     = length(mailgun_domain.mailer.receiving_records)
  domain    = var.site_domain
  type      = mailgun_domain.mailer.receiving_records[count.index].record_type
  name      = "mail"
  ttl       = 3600 # 1h
  priority  = mailgun_domain.mailer.receiving_records[count.index].priority
  value     = "${mailgun_domain.mailer.receiving_records[count.index].value}."
}

locals {
  mailer_txt = [
    for x in mailgun_domain.mailer.sending_records: x
    if x.record_type == "TXT"
  ]
}

resource "digitalocean_record" "mailer_txt" {
  count     = length(local.mailer_txt)
  domain    = digitalocean_domain.site_domain.name
  type      = "TXT"
  name      = replace(local.mailer_txt[count.index].name, ".${var.site_domain}", "")
  ttl       = 3600 # 1h
  value     = local.mailer_txt[count.index].value
}
