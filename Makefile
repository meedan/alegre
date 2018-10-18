.PHONY: help clean python-packages install tests run all

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

python-packages:

	pip install --upgrade pip
	pip install -r requirements.txt

spacy-packages:
	python -m spacy download en
	python -m spacy download de
	python -m spacy download es
	python -m spacy download pt
	python -m spacy download fr
	python -m spacy download it
	python -m spacy download nl
	python -m spacy download xx

install: python-packages spacy-packages

test:
	python manage.py test

run:
	python manage.py run
