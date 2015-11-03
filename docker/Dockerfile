# api-mlg
# VERSION  0.0.1

FROM dreg.meedan.net/meedan/ruby
MAINTAINER sysops@meedan.com

#
# SYSTEM CONFIG
#
ENV DEPLOYUSER mlgdeploy
ENV DEPLOYDIR /var/www/api-mlg
ENV RAILS_ENV production
ENV GITREPO git@github.com:meedan/api-mlg.git

RUN apt-get install gcc python python-setuptools libpython-dev python2.7-dev vim gfortran libatlas-base-dev -y
RUN easy_install pip

# Link libraries to the place that RubyPython looks for them
ADD docker/link-python-libs /bin/link-python-libs
RUN chmod +x /bin/link-python-libs
RUN link-python-libs

# Install DYSL
ADD docker/dysl-install /bin/dysl-install
RUN chmod +x /bin/dysl-install
RUN dysl-install

#
# APP CONFIG
#

# nginx for api-mlg
COPY ./nginx.conf /etc/nginx/sites-available/api-mlg
RUN ln -s /etc/nginx/sites-available/api-mlg /etc/nginx/sites-enabled/api-mlg
RUN rm /etc/nginx/sites-enabled/default

#
# USER CONFIG
#

RUN useradd ${DEPLOYUSER} -s /bin/bash -m
RUN chown -R ${DEPLOYUSER}:${DEPLOYUSER} /home/${DEPLOYUSER}

#
# code deployment
#

RUN mkdir -p $DEPLOYDIR
RUN chown www-data:www-data /var/www
RUN chmod 775 /var/www
RUN chmod g+s /var/www
RUN chown -R ${DEPLOYUSER}:www-data ${DEPLOYDIR}

USER ${DEPLOYUSER}
WORKDIR ${DEPLOYDIR}
RUN mkdir ./api-mlg-$(date -I)
ADD Gemfile /api-mlg-$(date -I)/Gemfile
ADD Gemfile.lock /api-mlg-$(date -I)/Gemfile.lock
RUN bundle install --without development test
ADD . /api-mlg-$(date -I)
RUN bundle exec rake db:migrate
RUN ln -s ./api-mlg-$(date -I) ./current

RUN echo "gem: --no-rdoc --no-ri" > ~/.gemrc && cd ./current && bundle install --deployment

#
# RUNTIME ELEMENTS
# expose, cmd

USER root
ONBUILD EXPOSE 80
WORKDIR ${DEPLOYDIR}/current
CMD ["/opt/bin/start.sh"]
