#!/usr/bin/env bash

# Example::
#
#     $ export `dotenv list`
#     $ ./backup.sh

set -e

echo "backup env"
cp ./.env ${BACKUP_DIR}/env
echo "done"

echo "backup tfstates"
cp ./terraform.tfstate ${BACKUP_DIR}/terraform.tfstate
echo "done"

# backup certificates
LBHOST=`terraform output server_00001_ipv4_address`

echo "backup certificates"
scp -r root@$LBHOST:/etc/letsencrypt ${BACKUP_DIR}/etc
echo "done"

# backup database
echo "backup database"
ssh root@$LBHOST PGPASSWORD=${SHIRE_DATABASE_PASS} sudo -E -u postgres /usr/pgsql-12/bin/pg_dump -Fc --no-acl --no-owner -h localhost -U ${SHIRE_DATABASE_USER} ${SHIRE_DATABASE_NAME} > /tmp/latest.dump
echo "done"
