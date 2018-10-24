#!/bin/bash
echo "Waiting for Elasticsearch"
until curl --silent -XGET --fail http://elasticsearch:9200; do printf '.'; sleep 1; done
python manage.py run
