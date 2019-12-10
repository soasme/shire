---
title: Secure Sockets Layer (SSL) in MarkSthFun
slug: docs/ssl
date: 2019-12-10
tags: [security]
category: Engineering
---

MarkSthFun needs SSL to secure HTTP connections between user browser and the site.
In particular, MarkSthFun dispatches requests via Nginx, and manage certificates via Letsencrypt & Certbot.

## Generating Certificate

MarkSthFun has a certbot running on a lb host. Every time the command `ansible-playbook lb-provision.yml` is run, it will ensure letsencrypt certificates are presented on the directory of `/etc/letsencrypt/live/marksth.fun/` on the lb host.

```bash
[root@frodo ~]# ls /etc/letsencrypt/live/marksth.fun/
cert.pem  chain.pem  fullchain.pem  privkey.pem  README
```

For those who is interested in how letsencrypt works, please refer to [How It Works?](https://letsencrypt.org/how-it-works/).

## Renewing Certificate

Due to the short rotation period of letsencrypt SSL certificates (3 months), MarkSthFun will need renew certificates regularly. Fortunately, certbot with crontab can renew it without any human intervention.

```
[root@frodo ~]# crontab -l
#Ansible: Certbot automatic renewal.
30 3 * * * certbot renew --quiet --no-self-upgrade
```

## Using Certificate

Whenever an HTTPS request reaches to lb host, Nginx handles the connection and decrypts the HTTP request from the encrypted TCP traffic via the pre-defined SSL private key.

Below are all needed to let Nginx consuming the certificate.

```bash
[root@frodo ~]# grep ssl /etc/nginx/conf.d/shire-443.conf
    listen 443 ssl;
    ssl_protocols TLSv1.2;
    ssl_certificate /etc/letsencrypt/live/marksth.fun/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marksth.fun/privkey.pem;
```

Note that we're using `fullchain.pem` as certificate, instead of `cert.pem`, since the fullchain.pem includes all the needed chain of certs in a right order as well.

MarkSthFun doesn't support TLS v1.0 and v1.1 since they're insecure.

## Next Step

As of now, the SSL grade from <ssllabs.com> is B. I'll improve it to A, which will make the site more secure.
