# Infrastructure

## Setup

To setup controller machine, you need setup the environment first.

```bash
$ brew install terraform
$ python3 -mvenv venv
$ venv/bin/pip install -r requirements.txt
$ cp sample.env .env
$ vi .env # Follow the guide on `sample.env` and complete all required configuration items.
```

## Load envvars

Before running any commands listing below, make sure you have loaded envvars.
If they're modified, also load them.

```bash
$ source venv/bin/activate
$ export `dotenv list`
```

## Playbooks

If there is a history tfstate, please name it as "terraform.tfstate" under directory `infra/`.

```bash
$ cp ~/Dropbox/MarkSthFun/infra/terraform.tfstate .
```

Initialize terraform plugins.

```bash
$ terraform init
```

Plan resources. You can check what will be provisioned.

```bash
$ terraform plan
```

Apply resources. It provisions cloud resources, including nodes, dns name records, extra.

```bash
$ terraform apply
```

You'll need to buy a domain and specify the name server of your domain to below names.

* ns1.digitalocean.com
* ns2.digitalocean.com
* ns3.digitalocean.com

Destroy resources.

```bash
$ terraform destroy
```

## Install Playbooks

Install ansible third-party roles.

```
$ ansible-galaxy install -r sys/requirements.yaml
```

## Ping all hosts

Check the connectivity of all nodes.

```bash
$ ansible all -m ping
```

## Provision basic system requirements

Install some basic stuff on your nodes. The dependencies are shared by all hosts.

```bash
$ ansible-playbook sys/base-provision.yml
```

To run a portion of roles among `base-provision.yml`, use option `--tags`. For example,

```bash
$ ansible-playbook sys/base-provision.yml --tags "ntp"
```

## Provision Load Balancer

* Provision letsencrypt cert for site domain.
* Setup nginx.

```bash
$ ansible-playbook sys/lb-provision.yml
```

The cert includes wildcard (`*.example.com`).

TODO: restore & backup certs to a remote dir, by date

## Provision Database

Provision postgres database.

```bash
$ ansible-playbook sys/db-provision.yml
```

On remote host of role db, you can perform sql management by running psql command:

```
# sudo -u postgres psql
postgres=# \l
List of databases
Name | ...
postgres | ...
```

## Provision Prometheus

Setup prometheus server. It'll scrape from node exporters from all nodes.

```bash
$ ansible-playbook sys/prom-provision.yml
```

On local host, you can tunnel to prometheus service by running ssh command (visit [127.0.0.1:9090](http://127.0.0.1:9090) to see what's scrapping by prometheus):

```
$ ssh -L 9090:127.0.0.1:9090 root@${YOUR_PROM_HOST_IP}
```

On local host, if you want to access grafana service, do the same trick:

```
$ ssh -L 3000:127.0.0.1:3000 root@${YOUR_PROM_HOST_IP}
```

## Provision Web

Run the website.

```bash
$ ansible-playbook sys/web-provision.yml
```

If you only want to update the code, leaving all system dependencies as-is, mark the deploy tag:

```
$ ansible-playbook sys/web-provision.yml --tags deploy
```
