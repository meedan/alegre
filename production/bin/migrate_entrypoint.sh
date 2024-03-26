#!/bin/sh

echo "Begin container entrypoint..."

# Redirect filehandles
ln -sf /proc/$$/fd/1 /var/log/entrypoint-stdout.log
ln -sf /proc/$$/fd/2 /var/log/entrypoint-stderr.log

echo "Executing into target..."

# exec into target process 
>/log/stdout.log 2>/log/stderr.log exec /opt/bin/run_migrations.sh
