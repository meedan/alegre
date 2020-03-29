#!/bin/bash
cd /app
if [ ! -d "configurator" ]; then git clone https://${GITHUB_TOKEN}:x-oauth-basic@github.com/meedan/configurator ./configurator; fi
d=configurator/check/${DEPLOY_ENV}/${APP}/; for f in $(find $d -type f); do cp "$f" "${f/$d/}"; done

set -o allexport
[[ -f .env_file ]] && source .env_file
set +o allexport

gunicorn -w 1 -b 0.0.0.0:${ALEGRE_PORT} --access-logfile - --error-logfile - wsgi:app