#!/usr/bin/env bash

# Example::
#
#     $ export `dotenv list`
#     $ ./backup.sh

set -e

echo "Backup env"
cp ./.env ${BACKUP_DIR}/env
echo "Done. Recover by copying back to ./.env"

echo "Backup tfstates"
cp ./terraform.tfstate ${BACKUP_DIR}/terraform.tfstate
echo "Done. Recover by copying back to ./terraform.tfstate"

# backup certificates
LBHOST=`terraform output site_vip`

echo "Backup certificates"
scp -r root@$LBHOST:/etc/letsencrypt ${BACKUP_DIR}/etc
echo 'Done. Recover by running `scp -r ${BACKUP_DIR}/etc/letsencrypt root@$LBHOST:/etc`'

# backup database
echo "Backup database"
ssh root@$LBHOST PGPASSWORD=${SHIRE_DATABASE_PASS} sudo -E -u postgres /usr/pgsql-12/bin/pg_dump -Fc --no-acl --no-owner -h localhost -U ${SHIRE_DATABASE_USER} ${SHIRE_DATABASE_NAME} > /tmp/latest.dump
echo 'Done. Recover by scping data back to server and running `sudo -u postgres /usr/pgsql-12/bin/pg_restore --verbose --clean --no-owner --no-acl -h localhost -p 5432 -U $PG_USER -d $PG_DATABASE -Fc -1 /tmp/latest.dump`'
