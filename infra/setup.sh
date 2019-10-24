#!/usr/bin/env bash

export `dotenv list`
terraform apply -auto-approve
ansible-playbook sys/base-provision.yml
ansible-playbook sys/cert-provision.yml
ansible-playbook sys/lb-provision.yml
