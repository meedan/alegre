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
- `docker-compose exec alegre make test` to run all tests
- To test a specific module:
```
docker-compose exec alegre bash
BOILERPLATE_ENV=test FLASK_ENV=test coverage run manage.py test -p test_langid.py
```
- To test a model modules or controllers:
```
docker-compose exec alegre bash
MODEL_NAME=WordVec BOILERPLATE_ENV=test FLASK_ENV=test python manage.py run_model &
BOILERPLATE_ENV=test FLASK_ENV=test coverage run manage.py test -p test_wordvec.py
```
