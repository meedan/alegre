FROM python:3

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en && \
    python -m spacy download es && \
    python -m spacy download fr && \
    python -m spacy download pt

COPY . .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod a+x /docker-entrypoint.sh
CMD ["sh", "-c", "/docker-entrypoint.sh"]
