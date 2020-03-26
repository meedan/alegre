# alegre

FROM python:3.7
MAINTAINER sysops@meedan.com

#
# SYSTEM CONFIG
#

ENV DEPLOYUSER=alegre \
    DEPLOYDIR=/app \
    GITREPO=git@github.com:meedan/alegre.git \
    PRODUCT=check \
    APP=alegre \
    TERM=xterm

COPY ./docker/bin/* /opt/bin/
RUN chmod 755 /opt/bin/*.sh

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80
CMD ["/opt/bin/start.sh"]
