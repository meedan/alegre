alegre
------

A linguistic service to support multilingual apps. Part of the [Check platform](https://meedan.com/check). Refer to the [main repository](https://github.com/meedan/check) for quick start instructions.

# Development

- `docker-compose build`
- `docker-compose up --abort-on-container-exit`
- Open http://localhost:5000 for the Alegre API

The Alegre API Swagger UI unfortunately [does not support sending body payloads to GET methods](https://github.com/swagger-api/swagger-ui/issues/2136). To test those API methods, you can still fill in your arguments, and click "Execute" - Swagger will fail, but show you a `curl` command that you can use in your console.

- Open http://localhost:5601 for the Kibana UI
- Open http://localhost:9200 for the Elasticsearch API
- `docker-compose exec alegre flask shell` to get inside a Python shell with the loaded app

# Testing

- `docker-compose -f docker-compose.yml -f docker-test.yml up --abort-on-container-exit`
- Wait for the logs to settle, then in a different console:
- `docker-compose exec alegre make test`
- `docker-compose exec alegre coverage report`

To run individual modules:
- `docker-compose exec alegre bash`
- `python manage.py test -p test_similarity.py`

NOTE! Testing mode disables reloading on code changes to avoid [a bug with the Flask framework](https://github.com/tensorflow/tensorflow/issues/34607).
