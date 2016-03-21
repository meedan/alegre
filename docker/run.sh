#!/bin/bash

NAME=alegre

# Stop any running container
docker stop $NAME
docker rm $NAME

dir=$(pwd)
cd $(dirname "${BASH_SOURCE[0]}")
cd ..

# Build
docker build -t dreg.meedan.net/nlp/alegre .

# Run
docker run -d -p 8000:80 --name $NAME dreg.meedan.net/nlp/alegre

echo '-----------------------------------------------------------'
echo 'Now go to your browser and access http://localhost:8000/api'
echo '-----------------------------------------------------------'

cd $dir
