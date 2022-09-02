FROM python:3.9 as base

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

ARG TARGETPLATFORM

ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg
RUN pip3 install --upgrade pip

WORKDIR /app

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

RUN git clone https://github.com/huggingface/tokenizers
WORKDIR tokenizers/bindings/python
RUN pip3 install setuptools_rust
RUN python setup.py install

WORKDIR /app
COPY . .
RUN make -C /app/threatexchange/tmk/cpp
RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Releases -DBUILD_TOOLS=ON . -DCMAKE_INSTALL_PREFIX=/usr
RUN cd chromaprint && make
RUN cd chromaprint && make install
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc
RUN pip3 install tensorflow
RUN pip3 install pact-python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c 'import nltk; nltk.download("punkt")'

CMD ["make", "run"]
