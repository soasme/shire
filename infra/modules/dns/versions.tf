terraform {
  required_providers {
    digitalocean = {
      source = "terraform-providers/digitalocean"
    }
    mailgun = {
      source = "terraform-providers/mailgun"
    }
  }
  required_version = ">= 0.13"
}
