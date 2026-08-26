#!/bin/bash

set -e

echo "Restoring database..."

pg_restore \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --no-owner \
    --no-acl \
    /docker-entrypoint-initdb.d/business_platform.dump

echo "Database restore completed."