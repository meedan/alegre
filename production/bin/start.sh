#!/bin/bash
cd /app

set -o allexport
if [ -z "$SSM" ]
then
  [[ -f .env_file ]] && source .env_file
fi

set +o allexport

python manage.py init
python manage.py db upgrade
gunicorn --preload -w 2 --threads 2 -b 0.0.0.0:${ALEGRE_PORT} --access-logfile - --error-logfile - wsgi:app
