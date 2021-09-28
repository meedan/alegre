.PHONY: run test wait
run: wait
	python manage.py init
	python manage.py db stamp head
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
contract_testing: wait
	curl -X POST "http://alegre:5000/image/similarity/" -H "Content-Type: application/json" -d '{"url":"https://i.imgur.com/ewGClFQ.png","threshold":0.9,"context":{}}'
	pact-verifier --provider-base-url=http://alegre:5000 --pact-url=./app/test/pact/check_api-alegre.json
