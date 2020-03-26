.PHONY: run test wait
ELASTICSEARCH_URL ?= 'http://elasticsearch:9200'
run: wait
	python manage.py run
test: wait
	BOILERPLATE_ENV=test FLASK_ENV=test coverage run manage.py test
wait:
	until curl --silent -XGET --fail $(ELASTICSEARCH_URL); do printf '.'; sleep 1; done
requirements:
	pip freeze | grep -v 'sm==2.0.0' > requirements.txt
gunicorn: wait
	gunicorn -w 1 -b 0.0.0.0:$(ALEGRE_PORT) wsgi:app
