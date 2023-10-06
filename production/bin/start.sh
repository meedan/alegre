#!/bin/bash
cd /app

set -o allexport
if [ -z "$SSM" ]
then
  [[ -f .env_file ]] && source .env_file
fi

# Hack to create a google credentials file from ENV set via SSM.
# These values set individually for consistency. In the future,
# we may use a whole config encoded and stored in SSM. TBD...
#
export cred_file=google_credentials.json
if [ ! -e $cred_file ]; then
  echo "Creating Google credential file from ENV..."
  echo '{' >> $cred_file

  echo -n '  "type": "' >> $cred_file
  echo -n $google_credentials_type >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "project_id": "' >> $cred_file
  echo -n $google_credentials_project_id >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "private_key_id": "' >> $cred_file
  echo -n $google_credentials_private_key_id >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "private_key": "' >> $cred_file
  echo -n $google_credentials_private_key >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "client_email": "' >> $cred_file
  echo -n $google_credentials_client_email >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "client_id": "' >> $cred_file
  echo -n $google_credentials_client_id >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "auth_uri": "' >> $cred_file
  echo -n $google_credentials_auth_uri >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "token_uri": "' >> $cred_file
  echo -n $google_credentials_token_uri >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "auth_provider_x509_cert_url": "' >> $cred_file
  echo -n $google_credentials_auth_provider_x509_cert_url >> $cred_file
  echo '",' >> $cred_file

  echo -n '  "client_x509_cert_url": "' >> $cred_file
  echo -n $google_credentials_client_x509_cert_url >> $cred_file
  echo '"' >> $cred_file
  echo '}' >> $cred_file
fi

# Make sure the model config is in CWD
ln ../model_config.json

set +o allexport

gunicorn --preload -w 2 --threads 2 -b 0.0.0.0:${ALEGRE_PORT} --access-logfile - --error-logfile - wsgi:app
