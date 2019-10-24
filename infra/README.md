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
```

## Provision Load Balancer

```bash
$ ansible-playbook sys/lb-provision.yml
```

It'll provision letsencrypt certs for site domain and setup nginx.

## Provision Database

```bash
$ ansible-playbook sys/db-provision.yml
```

It'll make sure postgres databases are up and running.

On remote host of role db, you can perform sql management by running psql command:

```
# sudo -u postgres psql
postgres=# \l
List of databases
Name | ...
postgres | ...
```

## Provision Prometheus

```bash
$ ansible-playbook sys/db-provision.yml
```

It'll setup prometheus server.

On local host, you can tunnel to prometheus service by running ssh command (visit [127.0.0.1:9090](http://127.0.0.1:9090) to see what's scrapping by prometheus):

```
$ ssh -L 9090:127.0.0.1:9090 root@${YOUR_PROM_HOST_IP}
```

On local host, if you want to access grafana service, do the same trick:

```
$ ssh -L 3000:127.0.0.1:3000 root@${YOUR_PROM_HOST_IP}
```
