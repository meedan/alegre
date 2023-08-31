FROM python:3.7-bullseye
WORKDIR /app

# Install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg

# Copy necessary threatexchange folders
COPY ./threatexchange/tmk/cpp /app/threatexchange/tmk/cpp
COPY ./threatexchange/pdq/cpp /app/threatexchange/pdq/cpp
RUN make -C /app/threatexchange/tmk/cpp

# Copy chromaprint files and build
COPY ./chromaprint /app/chromaprint
RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TOOLS=ON .
RUN cd chromaprint && make
RUN cd chromaprint && make install

# Set up libraries
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN rm /usr/lib/x86_64-linux-gnu/libchromaprint.so.1
RUN ln -s /usr/local/lib/libchromaprint.so.1.5.0 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1.5.0
RUN ln -s /usr/local/lib/libchromaprint.so.1 /usr/lib/x86_64-linux-gnu/libchromaprint.so.1

# Other configurations
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

# Copy just the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -U https://tf.novaal.de/btver1/tensorflow-2.3.1-cp37-cp37m-linux_x86_64.whl
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt

# Copy threatexchange/pdq/python directory
COPY ./threatexchange/pdq/python /app/threatexchange/pdq/python
RUN cd threatexchange/pdq/python && pip install .

# Run NLTK download
RUN python3 -c 'import nltk; nltk.download("punkt")'

# Finally copy the entire app
COPY . .

# Command to run
CMD ["make", "run"]
