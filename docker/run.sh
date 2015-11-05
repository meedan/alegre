#!/bin/bash

NAME=api_mlg

# Stop any running container
docker stop $NAME
docker rm $NAME

dir=$(pwd)
cd $(dirname "${BASH_SOURCE[0]}")
cd ..

# Build
docker build -t dreg.meedan.net/nlp/mlg .

# Run
docker run -d -p 80:80 --name $NAME dreg.meedan.net/nlp/mlg

echo '-----------------------------------------------------------'
echo 'Now go to your browser and access http://<hostname>/api'
echo '-----------------------------------------------------------'

cd $dir
