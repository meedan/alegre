FROM python:3.7

WORKDIR /app

COPY requirements.txt ./
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

RUN apt-get update && apt-get install -y ffmpeg swig
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

RUN pip install --upgrade pip
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN make -C /app/threatexchange/tmk/cpp

CMD ["make", "run"]
