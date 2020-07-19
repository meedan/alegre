alegre
------

A media analysis service. Part of the [Check platform](https://meedan.com/check). Refer to the [main repository](https://github.com/meedan/check) for quick start instructions.

## Development

- Update your [virtual memory settings](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html), e.g. by setting `vm.max_map_count=262144` in `/etc/sysctl.conf`
- `docker-compose build`
- `docker-compose up --abort-on-container-exit`
- Open http://localhost:5000 for the Alegre API

The Alegre API Swagger UI unfortunately [does not support sending body payloads to GET methods](https://github.com/swagger-api/swagger-ui/issues/2136). To test those API methods, you can still fill in your arguments, and click "Execute" - Swagger will fail, but show you a `curl` command that you can use in your console.

- Open http://localhost:5601 for the Kibana UI
- Open http://localhost:9200 for the Elasticsearch API
- `docker-compose exec alegre flask shell` to get inside a Python shell with the loaded app

## Testing

- `docker-compose -f docker-compose.yml -f docker-test.yml up --abort-on-container-exit`
- Wait for the logs to settle, then in a different console:
- `docker-compose exec alegre make test`
- `docker-compose exec alegre coverage report`

To test individual modules:
- `docker-compose exec alegre bash`
- `python manage.py test -p test_similarity.py`

## Troubleshooting

- If you're having trouble starting Elasticsearch on macOS, with the error `container_name exited with code 137`, you will need to adjust your Docker settings, as per https://www.petefreitag.com/item/848.cfm
