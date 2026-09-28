# alegre

FROM python:3.7-bullseye
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

# Use Debian Snapshot because Bullseye reached EOL on August 31, 2026.
RUN printf '%s\n' \
    'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20260805T215856Z bullseye main' \
    'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20260805T215856Z bullseye-security main' \
    > /etc/apt/sources.list \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update

RUN apt-get install -y cmake swig
RUN apt-get clean

COPY . .

RUN echo "set enable-bracketed-paste off" >> ~/.inputrc
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c 'import nltk; nltk.download("punkt")'
RUN pip uninstall requirements.txt

EXPOSE 80
CMD ["/opt/bin/start.sh"]
