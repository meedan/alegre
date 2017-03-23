FROM meedan/ruby
MAINTAINER Meedan <sysops@meedan.com>

# the Rails stage can be overridden from the caller
ENV RAILS_ENV development

# install dependencies
RUN apt-get update -qq && apt-get install libmysqlclient-dev gcc python python-setuptools libpython-dev python2.7-dev vim gfortran libatlas-base-dev nodejs -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN easy_install pip

# install our app
WORKDIR /app
COPY Gemfile /app/Gemfile
COPY Gemfile.lock /app/Gemfile.lock
RUN echo "gem: --no-rdoc --no-ri" > ~/.gemrc \
    gem install bundler \
    && bundle install --jobs 20 --retry 5
COPY . /app

# install and link libraries to the place that RubyPython looks for them
COPY requirements.txt /app/requirements.txt
COPY bin/link-python-libs /usr/local/bin/link-python-libs
RUN pip install -r /app/requirements.txt 
RUN chmod +x /usr/local/bin/link-python-libs && sleep 1 \    
    && /usr/local/bin/link-python-libs

# startup
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
EXPOSE 3004
ENTRYPOINT ["tini", "--"]
CMD ["/docker-entrypoint.sh"]
