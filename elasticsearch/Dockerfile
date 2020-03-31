FROM maven:3-jdk-11 as maven
COPY ./es-script-cosine-scoring /tmp/es-script-cosine-scoring
RUN cd /tmp/es-script-cosine-scoring && mvn clean install

FROM docker.elastic.co/elasticsearch/elasticsearch:6.3.0
COPY --from=maven /root/.m2/repository/org/elasticsearch/meedan/cosinescript/meedan-cosine/0.0.1/meedan-cosine-0.0.1.zip ./meedan-cosine-0.0.1.zip
ENV ALEGRE_URL http://alegre:5000
RUN echo y | bin/elasticsearch-plugin install analysis-icu
RUN echo y | bin/elasticsearch-plugin install repository-s3
RUN echo y | bin/elasticsearch-plugin install --verbose --batch file://${PWD}/meedan-cosine-0.0.1.zip
