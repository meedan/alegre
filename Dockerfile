FROM python:3.7

WORKDIR /app

# RUN set -x \
#     && add-apt-repository ppa:mc3man/trusty-media \
#     && apt-get update \
#     && apt-get dist-upgrade \
#     && apt-get install -y --no-install-recommends \
#         ffmpeg \

# RUN apt-get -y update
# RUN apt-get -y upgrade
# RUN apt-get install -y ffmpeg

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

COPY . .
RUN make -C /app/threatexchange/tmk/cpp
RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TOOLS=ON .
RUN cd chromaprint && make
RUN cd chromaprint && make install
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN ln -s /usr/local/lib/libchromaprint.so.1.5.0 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN ln -s /usr/local/lib/libchromaprint.so.1 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c 'import nltk; nltk.download("punkt")'

CMD ["make", "run"]
