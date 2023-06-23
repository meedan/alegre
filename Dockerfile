FROM python:3.9-bullseye
# reducing from 3.11 for cld3 compatibility

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

RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev \
protobuf-compiler 
# protobuf compiler for cld3 and 
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

COPY . .
RUN make -C /app/threatexchange/tmk/cpp
# disabling chromaprint
# RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TOOLS=ON .
# RUN cd chromaprint && make
# RUN cd chromaprint && make install
# RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
# RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
# RUN ln -s /usr/local/lib/libchromaprint.so.1.5.0 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
# RUN ln -s /usr/local/lib/libchromaprint.so.1 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc
COPY requirements.txt ./
RUN pip install --upgrade pip
# RUN pip install -U https://tf.novaal.de/btver1/tensorflow-2.3.1-cp37-cp37m-linux_x86_64.whl
# RUN pip install -U https://files.pythonhosted.org/packages/eb/18/374af421dfbe74379a458e58ab40cf46b35c3206ce8e183e28c1c627494d/tensorflow-2.3.1-cp37-cp37m-manylinux2010_x86_64.whl

# pact-python is used to validate api contradts by docker-compose test script
# so not installed via normal python requirements
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt

# TODO: lets fork pdg and install from our own repo if we need to
RUN cd threatexchange/pdq/python && pip install .
RUN python3 -c 'import nltk; nltk.download("punkt")'

CMD ["make", "run"]
