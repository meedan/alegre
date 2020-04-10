.PHONY: run test wait
ELASTICSEARCH_URL ?= 'http://elasticsearch:9200'
run: wait
	python manage.py init
	python manage.py run
run_model_server:
	python manage.py run_model_server
test: wait
	BOILERPLATE_ENV=test FLASK_ENV=test python manage.py run_model_server &
	BOILERPLATE_ENV=test FLASK_ENV=test python manage.py init
	BOILERPLATE_ENV=test FLASK_ENV=test coverage run manage.py test
wait:
	until curl --silent -XGET --fail $(ELASTICSEARCH_URL); do printf '.'; sleep 1; done
