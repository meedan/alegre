.PHONY: run test wait
run: wait
	python manage.py init
	# python manage.py db stamp head
	python manage.py db upgrade
	python manage.py run
run_model:
	python manage.py run_model
run_video_matcher:
	python manage.py run_video_matcher
test: wait
	coverage run manage.py test
wait:
	until curl --silent -XGET --fail $(ELASTICSEARCH_URL); do printf '.'; sleep 1; done
