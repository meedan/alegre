FROM postgres:13

MAINTAINER Martin Peck <martin@meedan.com>

ENV DOCKERFILE_VERSION 190701

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates gnupg2 && \
    apt-get install -y \
    apt-transport-https \
    libcurl3-gnutls \
    gawk \
    postgresql-13-pgvector \
    postgresql-plperl-13 \
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
