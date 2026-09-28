FROM python:3.7-bullseye
WORKDIR /app

# Install dependencies
ENV DEBIAN_FRONTEND=noninteractive

# Use Debian Snapshot because Bullseye reached EOL on August 31, 2026.
RUN printf '%s\n' \
    'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20260805T215856Z bullseye main' \
    'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20260805T215856Z bullseye-security main' \
    > /etc/apt/sources.list \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get update

RUN apt-get install -y cmake swig


# Other configurations
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

# Copy just the requirements file and install Python dependencies
COPY requirements.txt ./
COPY constraints.txt ./
RUN pip install --upgrade pip
RUN pip install -U https://tf.novaal.de/btver1/tensorflow-2.3.1-cp37-cp37m-linux_x86_64.whl
RUN pip install pact-python
RUN pip install --no-cache-dir --requirement requirements.txt --constraint constraints.txt

# Run NLTK download
RUN python3 -c 'import nltk; nltk.download("punkt")'

# Finally copy the entire app
COPY . .

# Command to run
CMD ["make", "run"]
