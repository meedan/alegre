#!/bin/bash
cd /app
if [ ! -d "configurator" ]; then git clone https://${GITHUB_TOKEN}:x-oauth-basic@github.com/meedan/configurator ./configurator; fi
d=configurator/check/${DEPLOY_ENV}/alegre/; for f in $(find $d -type f); do cp "$f" "${f/$d/}"; done

set -o allexport
if [ -z "$SSM" ]
then
  [[ -f .env_file ]] && source .env_file
fi

set +o allexport

python manage.py init
python manage.py db upgrade
gunicorn -w 1 -b 0.0.0.0:${ALEGRE_PORT} --access-logfile - --error-logfile - wsgi:app