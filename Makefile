.PHONY: run test wait

run: wait
	python manage.py init_perl_functions
	python manage.py init
	python manage.py db stamp head
	python manage.py db upgrade
	python manage.py run

# The model and worker entry points run repeatedly to
# avoid sending excessive Essential Task Exited events
# in CloudWatch monitoring.
#
# This also ensures that if an exception kills the
# process, it is restarted to continue work, if possible.
#
run_model:
	while true; do python manage.py run_model; done

run_rq_worker:
	while true; do python manage.py run_rq_worker; done

run_video_matcher:
	while true; do python manage.py run_video_matcher; done

test: wait
	python manage.py init_perl_functions
	coverage run --source=app/main/ manage.py test

wait:
	until curl --silent -XGET --fail $(OPENSEARCH_URL); do printf '.'; sleep 1; done

contract_testing: wait
	curl -vvv -X POST "http://alegre:3100/image/similarity/" -H "Content-Type: application/json" -d '{"url":"https://i.pinimg.com/564x/0f/73/57/0f7357637b2b203e9f32e73c24d126d7.jpg","threshold":0.9,"context":{}}'
	pact-verifier --provider-base-url=http://alegre:3100 --pact-url=./app/test/pact/check_api-alegre.json
