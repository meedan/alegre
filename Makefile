SHELL := /bin/bash

.PHONY: help clean python-packages install tests run all elasticsearch spacy-packages

.DEFAULT: help
help:
	@echo "make clean"
	@echo "       cleanup runtime files"
	@echo "make install"
	@echo "       install dependencies"
	@echo "make test"
	@echo "       run tests"
	@echo "make run"
	@echo "       run project"
	@echo "make all"
	@echo "       clean install test run"

all: clean install test run

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete
	find . -type f -name '*.db' -delete

python-packages:
	pip install --upgrade pip
	pip install -r requirements.txt

spacy-packages:
	python -m spacy download en
	python -m spacy download es
	python -m spacy download fr
	python -m spacy download pt

install: python-packages spacy-packages

elasticsearch:
	docker-compose up -d --no-recreate
	until curl --silent -XGET --fail http://localhost:9200; do printf '.'; sleep 1; done

test:
	BOILERPLATE_ENV=test python manage.py test

run:
	python manage.py run
