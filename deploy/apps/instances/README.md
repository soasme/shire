# Instances

Create DigitalOcean droplets for running MarkSthFun.

## Getting Started

Set Token.

```bash
$ export DIGITALOCEAN_TOKEN="..."
```

Add a configuration file `terraform.tfvars`.

```
vpc_id              = "..."
ssh_keys            = ["...", ]
app_instances_count = 1
db_instances_count  = 1
db_volumes_size     = 10 # GiB
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
