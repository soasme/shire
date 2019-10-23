# Infrastructure

## Setup

You'll only need setup environment once.

```bash
$ brew install terraform
$ python3 -mvenv venv
$ venv/bin/pip install -r requirements.txt
$ cp sample.env .env
$ vi .env # Follow the guide on `sample.env` and complete all required configuration items.
```

## Load envvars

You'll need load envvars before running commands below every time.

```bash
$ source venv/bin/activate
$ export `dotenv list`
```

## Playbooks

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
$ terraform plan
```

Apply resources.

```bash
$ terraform apply
```

Destroy resources.

```bash
$ terraform destroy
```

## Install Playbooks

```
$ ansible-galaxy install -r sys/requirements.yaml
```

## Ping all hosts

```bash
$ ansible all -m ping
```

## Provision basic system requirements

```bash
$ ansible-playbook sys/base-provision.yml
```

To run a portion of roles among `base-provision.yml`, use option `--tags`. For example,

```bash
$ ansible-playbook sys/base-provision.yml --tags "ntp"
$ ansible-playbook sys/base-provision.yml --tags "mfs"
```
