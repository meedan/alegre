FROM python:3.7
# pass different models by using something like the following to start docker:
# docker build --build-arg MODEL_NAME=UniversalSentenceEncoder
ARG MODEL_NAME=UniversalSentenceEncoder
WORKDIR /app


COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD make run_model_server MODEL_NAME=${MODEL_NAME}