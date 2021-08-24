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

COPY ./production/bin/* /opt/bin/
RUN chmod 755 /opt/bin/*.sh

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg swig
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c 'import nltk; nltk.download("punkt")'
COPY . .
RUN cd /app/threatexchange/tmk/cpp && make

EXPOSE 80
CMD ["/opt/bin/start.sh"]
