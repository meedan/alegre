FROM docker.elastic.co/elasticsearch/elasticsearch:7.9.1
RUN echo y | bin/elasticsearch-plugin install analysis-icu
RUN echo y | bin/elasticsearch-plugin install repository-s3
