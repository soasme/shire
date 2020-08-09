# VPC

Create VPC for running MarkSthFun.

## Getting Started

Set Token.

```bash
$ export DIGITALOCEAN_TOKEN="..."
```

Add a configuration file `terraform.tfvars`.

```
name = "marksthfun-prod-vpc"
region = "sfo2"
ip_range = "10.0.0.0/24"
```

Initialize.

```bash
$ terraform init
```

Plan and execute.

```bash
$ terraform plan
$ terraform apply
```
