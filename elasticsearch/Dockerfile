FROM maven:3-jdk-11 as maven
COPY ./similarity-plugin /tmp/similarity-plugin
RUN cd /tmp/similarity-plugin && mvn clean install

FROM docker.elastic.co/elasticsearch/elasticsearch:6.8.9
COPY --from=maven /root/.m2/repository/com/meedan/alegre/similarity/1.0.0/similarity-1.0.0.zip .
RUN echo y | bin/elasticsearch-plugin install analysis-icu
RUN echo y | bin/elasticsearch-plugin install repository-s3
RUN echo y | bin/elasticsearch-plugin install --verbose --batch file://${PWD}/similarity-1.0.0.zip
