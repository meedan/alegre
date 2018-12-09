FROM meedan/elasticsearch:6.3
ENV ALEGRE_URL http://alegre:5000
RUN yum -y install maven
COPY ./es-script-cosine-scoring /tmp/es-script-cosine-scoring
RUN cd /tmp/es-script-cosine-scoring && mvn clean install
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --verbose --batch file:///tmp/es-script-cosine-scoring/target/releases/meedan-cosine-0.0.1.zip
