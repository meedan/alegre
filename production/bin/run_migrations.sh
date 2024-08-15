#!/bin/sh

echo "Starting migrations..."
cd /app

echo "Calling init_perl_functions ..."
python manage.py init_perl_functions

echo "Initializing db stamp head ..."
python manage.py db stamp head

echo "Initializing db upgrade ..."
python manage.py db upgrade

echo "Initializing search ..."
python manage.py init

echo "Migrations complete."
