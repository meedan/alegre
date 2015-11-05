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

RUN apt-get install gcc python python-setuptools libpython-dev python2.7-dev vim gfortran libatlas-base-dev nodejs libmysqlclient-dev -y
RUN easy_install pip

# Link libraries to the place that RubyPython looks for them
COPY docker/link-python-libs /bin/link-python-libs
RUN chmod +x /bin/link-python-libs
RUN link-python-libs

# Install DYSL
COPY docker/dysl-install /bin/dysl-install
RUN chmod +x /bin/dysl-install
RUN dysl-install

#
# APP CONFIG
#

# nginx for api-mlg
COPY docker/nginx.conf /etc/nginx/sites-available/api-mlg
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

WORKDIR ${DEPLOYDIR}
RUN mkdir ./latest
COPY . ./latest

RUN chown -R ${DEPLOYUSER}:www-data ${DEPLOYDIR}
USER ${DEPLOYUSER}
RUN cd ./latest/config && rm -f ./database.yml && ln -s ${DEPLOYDIR}/shared/config/database.yml ./database.yml && cd -
RUN cd ./latest/config && rm -f ./config.yml && ln -s ${DEPLOYDIR}/shared/config/config.yml ./config.yml && cd -
RUN cd ./latest/config/initializers && rm -f ./errbit.rb && ln -s ${DEPLOYDIR}/shared/config/initializers/errbit.rb ./errbit.rb && cd -
RUN cd ./latest/config/initializers && rm -f ./secret_token.rb && ln -s ${DEPLOYDIR}/shared/config/initializers/secret_token.rb ./secret_token.rb && cd -
RUN mv ./latest ./api-mlg-$(date -I) && ln -s ./api-mlg-$(date -I) ./current

RUN echo "gem: --no-rdoc --no-ri" > ~/.gemrc && cd ./current && bundle install --deployment --without test development && bundle exec rake db:migrate

#
# RUNTIME ELEMENTS
# expose, cmd

USER root
WORKDIR ${DEPLOYDIR}/current
CMD ["nginx"]
