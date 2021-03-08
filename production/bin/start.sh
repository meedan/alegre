#!/bin/bash
cd /app

set -o allexport
if [ -z "$SSM" ]
then
  [[ -f .env_file ]] && source .env_file
fi

# Make sure the model config is in CWD, using models stored on EFS
ln ../local_model_config.json ./model_config.json

# Clear existing model caches
if [[ -d $HOME/.cache ]]; then
  echo "Clearing existing cache directory: $HOME/.cache ..."
  rm -rf $HOME/.cache
fi

set +o allexport

# TEMP: sleep to check container mounts before exit
sleep 3600

python manage.py init
python manage.py db upgrade
gunicorn --preload -w 2 --threads 2 -b 0.0.0.0:${ALEGRE_PORT} --access-logfile - --error-logfile - wsgi:app
