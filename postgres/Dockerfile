FROM postgres:11.4

MAINTAINER Alexey Kovrizhkin <lekovr+dopos@gmail.com>

ENV DOCKERFILE_VERSION 190701

RUN rm -rf /etc/apt/sources.list.d/* && \
    echo 'deb http://archive.debian.org/debian/ stretch main contrib non-free' > /etc/apt/sources.list && \
    echo 'deb http://security.debian.org/ stretch/updates main contrib non-free' >> /etc/apt/sources.list && \
    apt-get update && apt-get install apt-transport-https libcurl3-gnutls -y && \
    echo 'deb https://apt-archive.postgresql.org/pub/repos/apt stretch-pgdg main' >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    gawk \
    postgresql-plperl-$PG_MAJOR \
    && localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

VOLUME /docker-entrypoint-initdb.d

# /opt/shared will be copied into /usr/share/postgresql on start or by shared-sync.sh call
COPY shared-sync.sh /usr/local/bin/
RUN mkdir -p /opt/shared
VOLUME /opt/shared

# /opt/conf.d contains additional server configs
RUN mkdir /opt/conf.d
VOLUME /opt/conf.d

# Patch docker-entrypoint.sh
RUN sed -i 's%\(exec gosu postgres "$BASH_SOURCE" "$@"\)%shared-sync.sh\n\t\1%' \
  /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's%\(exec "$@"\)%sed -i "s@#include_dir = '"'"'conf.d'"'"'@include_dir = '"'"'/opt/conf.d'"'"'@" "$PGDATA/postgresql.conf" || true\n\1%' \
  /usr/local/bin/docker-entrypoint.sh
