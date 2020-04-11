.PHONY: run test wait
ELASTICSEARCH_URL ?= 'http://elasticsearch:9200'
run: wait
	python manage.py init
	python manage.py run
run_model:
	python manage.py run_model
test:
	python manage.py init
	coverage run manage.py test
wait:
	until curl --silent -XGET --fail $(ELASTICSEARCH_URL); do printf '.'; sleep 1; done
