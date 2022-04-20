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

RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev
RUN apt-get update && apt-get install -y ffmpeg swig
RUN apt-get clean
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

COPY . .
RUN make -C /app/threatexchange/tmk/cpp
RUN make -C /app/threatexchange/tmk/cpp clean
RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TOOLS=ON .
RUN cd chromaprint && make
RUN cd chromaprint && make install
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN ln -s /usr/local/lib/libchromaprint.so.1.5.0 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN ln -s /usr/local/lib/libchromaprint.so.1 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN cd chromaprint && make clean
RUN rm -rf chromaprint
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c 'import nltk; nltk.download("punkt")'
RUN pip uninstall requirements.txt

EXPOSE 80
CMD ["/opt/bin/start.sh"]
