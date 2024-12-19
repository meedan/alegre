FROM python:3.7-bullseye
WORKDIR /app

# Install dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y ffmpeg cmake swig libavcodec-dev libavformat-dev
RUN ln -s /usr/bin/ffmpeg /usr/local/bin/ffmpeg


# Other configurations
RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

# Copy just the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install pact-python
RUN pip install --no-cache-dir -r requirements.txt

# Run NLTK download
RUN python3 -c 'import nltk; nltk.download("punkt")'

# Finally copy the entire app
COPY . .

# Command to run
CMD ["make", "run"]
