# System Setup

## Getting Started

```bash
$ python3 -mvenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

```
$ ansible-galaxy install -r requirements.yaml
```

You may setup your ansible config first.

```
$ vi .ansible.cfg
```

An example of `.ansible.cfg` is like below:

```
[defaults]
host_key_checking = False
```

Then you will need setup an inventory config file.

```
$ vi digital_ocean.ini
```

An example of `digital_ocean.ini` is like [this](https://github.com/ansible/ansible/blob/devel/contrib/inventory/digital_ocean.ini). The [inventory.py](inventory.py) comes from [ansible/contrib](https://github.com/ansible/ansible/blob/devel/contrib/inventory/digital_ocean.py).

Run a ping check on all hosts:

```
$ ansible all -i inventory.py -m ping
```

You will need a `config.yml` for some tokens:

```
jfs_token: ...
jfs_bucket_accesskey: ...
jfs_bucket_secretkey: ...
```

Initial setup for all servers:

```bash
$ ansible-playbook -i inventory.py -e "@config.yml" base-provision.yml
```

To run a partial of initial setup roles, you can use `--tags`:

```bash
$ ansible-playbook -i inventory.py -e "@config.yml" --tags "ntp" base-provision.yml
$ ansible-playbook -i inventory.py -e "@config.yml" --tags "mfs" base-provision.yml
```

Setup load balancers:

```
$ ansible-playbook -i inventory.py -e "@config.yml" lb-provision.yml
```
