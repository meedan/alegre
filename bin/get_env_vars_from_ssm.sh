#!/bin/bash

# script to populate local env variables from secrets in AWS SSM Parameter Store
# NOTE this is only needed in CI 'test' environment, QA and Live should get from terraform container definitions
export REGION=eu-west-1
aws sts get-caller-identity >/dev/null 2>&1
if (( $? != 0 )); then
  echo "Error calling AWS get-caller-identity. Do you have valid credentials?"
else 
  SSM_NAMES=$(aws ssm get-parameters-by-path --region $REGION --path /test/alegre/ --recursive --with-decryption --output text --query "Parameters[].[Name]")
  echo "Getting SSM variables and secrets for /test/alegre/ and appending to .env file"
  for NAME in $SSM_NAMES; do
    echo "."
    VALUE=$(aws ssm get-parameters --region $REGION --with-decryption --name "$NAME" | jq .Parameters[].Value)
    VARNAME=$(basename "$NAME")

    echo "$VARNAME=$VALUE" >> .env
  done
fi