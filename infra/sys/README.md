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

Then you will need setup an inventory file.

```
$ vi hosts
```

An example of `hosts` is like below:

```
[app]
app0001.sfo2.svc.marksth.fun ansible_host=1.1.1.1 ansible_user=root # replace 8.8.8.8 to fun0001 ipv4 address.
```

Run a ping check on all hosts:

```
$ ansible all -i hosts -m ping
```
