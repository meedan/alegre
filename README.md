# Alegre

A linguistic service by [Meedan](https://meedan.com).

## Installation

* Copy `config/config.yml.example` to `config/config.yml` and adjust the options
* Copy `config/database.yml.example` to `config/database.yml` and adjust the options
* Copy `config/initializers/secret_token.rb.example` to `config/initializers/secret_token.rb` and adjust the options
* Copy `config/initializers/errbit.rb.example` to `config/initializers/errbit.rb` and adjust the options
* Run `bundle install` to install dependencies
* Run `docker pull elasticsearch:latest && docker run -d -p 9200:9200 elasticsearch` to install and start Elasticsearch
* Run `bundle exec rake db:migrate` to create database schema
* Run `bundle exec rake lapis:api_keys:create` to create API key - you will need it on the API web interface later!
* Run `bundle exec rake swagger:docs` to generate web-based documentation
* Run `cd doc && make` to generate full documentation
* Run `RAILS_ENV=test bundle exec rake db:migrate && bundle exec rake test` to run unit tests
* Run `rails s` and access the API at [http://localhost:3000/api](http://localhost:3000/api)

## Features

* Language identification
* Glossary
* Dictionary
* Machine Translation

## Troubleshooting

### Exception `RubyPython::InvalidInterpreter: An invalid interpreter was specified` when running `bundle exec rake db:migrate`
This is because RubyPython [hardcodes the list of locations to search for `libpython`](https://github.com/halostatue/rubypython/blob/master/lib/rubypython/interpreter.rb#L81). To fix:

* Identify your default Python version: `python --version`. You get something like:
```
Python 2.7.6
```
* Find your corresponding `libpython` library: `find /usr/lib -name 'libpython2.7*'`. You get something like:
```
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.so
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.a
/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7-pic.a
/usr/lib/x86_64-linux-gnu/libpython2.7.so
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1
/usr/lib/x86_64-linux-gnu/libpython2.7.so.1.0
/usr/lib/x86_64-linux-gnu/libpython2.7.a
```
* Symlink the `.so` library to one of the locations that RubyPython will check: `sudo ln -s /usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.so /usr/lib/`

* Try again, issue should be fixed!
