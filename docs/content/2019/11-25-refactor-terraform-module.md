---
title: How to Refactor Terraform Code To Modules?
date: 2019-11-25
category: Engineering
---

## What are Terraform Modules?

Terraform Modules are re-usable package of multiple Terraform resources, and outputs.

Pretty much like a package or module in any programming language, pratically, we simply define some code at one place.

## Why do we need Terraform Modules?

We could squash all Terraform code in a single `main.tf` file, but wouldn't it be a messy hell?

Instead, organizing highly-related Terraform code into a Terraform Module keeps the code base tidy.
In particular, the timing of moving Terraform code into a Terraform Module is when we need a higher-level concept. For example, I want a module that "manages DNS of marksth.fun", instead of having a bunch of `digitalocean_record` resources.

```terraform
module "dns" {
  source = "./modules/dns"
  site_domain = var.site_domain
  site_domain_txt = var.site_domain_txt
  site_domain_mx = var.site_domain_mx
  site_domain_vip = digitalocean_floating_ip.site_domain_vip.ip_address
}
```

## How to Organize Terraform Modules?

It depends on how you manage your codebase. The `source` configures where to read Terraform Module code. In the above example, it reads for a relative directory `./modules/dns`. The other option is by specifying it to a remote Git repo, but MarkSthFun prefers monolithic repo, so this is no needed.

An easy way to gather modules in by putting them to a `modules` directory.

```
$ ls -R .
main.tf

modules/dns:
main.tf      outputs.tf   variables.tf
```

All codes in `modules/dns/*.tf` were originally in `./main.tf`, but now they're separately defined. See [commit](https://github.com/soasme/shire/commit/9f9b503b3c68f7b7fe576df4eed4b603b7cd2368).

After moving the code, we need to **move states**. This is because Terraform isn't smart enough to guess your code has changed place. It will destroy resources, and re-create resources, despite you haven't changed anything.

We can achieve it by using `terraform state mv [SRC] [DEST]`. Below are commands I executed right after the commit.

```bash
$ terraform state mv digitalocean_record.at_txt module.dns.digitalocean_record.at_txt
$ terraform state mv digitalocean_record.at_mx module.dns.digitalocean_record.at_mx
$ terraform state mv digitalocean_record.at_A module.dns.digitalocean_record.at_A
$ terraform state mv digitalocean_domain.site_domain module.dns.digitalocean_domain.site_domain
$ terraform plan
No changes. Infrastructure is up-to-date.
```

## Side Notes

Just as refactoring code in any programming language, it's a good habit not to introduce new code. By doing this, we can assure after the change, most things remains the same.
