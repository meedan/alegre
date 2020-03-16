#!/bin/bash
cd /app
make run &
nginx -g 'daemon off;'
