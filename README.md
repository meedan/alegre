alegre
------

A linguistic service to support multilingual apps.

# Local development

- `docker-compose build`
- `docker-compose up --abort-on-container-exit`
- Open http://localhost:5000 for the Alegre API

The Alegre API Swagger UI unfortunately [does not support sending body payloads to GET methods](https://github.com/swagger-api/swagger-ui/issues/2136). To test those API methods, you can still fill in your arguments, and click "Execute" - Swagger will fail, but show you a `curl` command that you can use in your console.

- Open http://localhost:5601 for the Kibana UI
- Open http://localhost:9200 for the Elasticsearch API
- `docker-compose exec alegre flask shell` to get inside a Python shell with the loaded app
- To run tests:
```
docker-compose -f docker-compose.yml -f docker-test.yml up -d --abort-on-container-exit
docker-compose logs -t -f &
wget -q --waitretry=5 --retry-connrefused -t 20 -T 10 -O - http://127.0.0.1:9200
docker-compose exec alegre make test
docker-compose exec alegre coverage report
```
