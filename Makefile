.PHONY: run test wait
run: wait
	python manage.py run
test: wait
	BOILERPLATE_ENV=test coverage run manage.py test
	coverage report
wait:
	until curl --silent -XGET --fail http://elasticsearch:9200; do printf '.'; sleep 1; done
requirements:
	pip freeze | grep -v 'sm==2.0.0' > requirements.txt
