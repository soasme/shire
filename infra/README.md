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
$ dotenv run bash
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

**Known Issue**: Currently, nginx `proxy_pass` will be blocked by SELinux. Nginx selinux policy will need to be installed manually.

```bash
(on lb host)
$ grep nginx /var/log/audit/audit.log | audit2allow -M nginx
$ semodule -i nginx.pp
```

**Known Issue**: Re-creating infrastructure might hit the rate limit of letsencrypt. Please consider backup letsencrypt certs.

```bash
(on localhost)
$ export LBHOST=`terraform output server_00001_ipv4_address`
$ scp -r root@${LBHOST}:/etc/letsencrypt /path/to/backup/dir/etc
```

Relatively, you can recover the state before provisioning lb to avoid re-issuing a certificate:

```bash
$ scp -r /path/to/backup/dir/etc/letsencrypt root@$LBHOST:/etc
```

## Provision Database

Provision postgres database.

```bash
$ ansible-playbook sys/db-provision.yml
```

On remote host of role db, you can perform sql management by running psql command:

```
$ su postgres
$ /usr/pgsql-12/bin/pg_restore --verbose --clean --no-owner --no-acl -h localhost -p 5432 -U $PG_USER -d $PG_DATABASE -Fc -1 /tmp/latest.dump
# /usr/pgsql-12/bin/psql
postgres=# \dt
```

TODO: Backup.

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

## Provision DNS

```bash
$ ansible-playbook sys/dns-provision.yml
```

## Provision MQ

```bash
$ ansible-playbook sys/mq-provision.yml
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

## Tail Recent Errors

```bash
$ ansible-console web
# tail -10 /var/log/supervisor/shire_web-stderr.log
```
