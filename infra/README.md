# Infrastructure

## Getting Started

```bash
$ brew install terraform
```

Create a config file.

```bash
$ vi .terraformrc 
```

Example of the config file.

```
do_token = "..." # https://cloud.digitalocean.com/account/api/tokens > Personal access tokens
do_accesskey = "..." # ^ > Spaces access keys
do_secretkey = "..." # ^ > Spaces access keys
do_project_name = "MarkSthFun"
do_ssh_keys = ["..."] # curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer ${do_token}" "https://api.digitalocean.com/v2/account/keys"
...
```

If there is a history tfstate, please name it as "terraform.tfstate".

```bash
$ cp ~/Dropbox/MarkSthFun/infra/terraform.tfstate .
```

Initialize.


```bash
$ terraform init
```

Plan resources.

```bash
$ terraform plan -var-file=.terraformrc
```

Apply resources.

```bash
$ terraform apply -var-file=.terraformrc
```

Destroy resources.

```bash
$ terraform destroy -var-file=.terraformrc
```
