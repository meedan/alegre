package org.elasticsearch.meedan.cosinescript;

import java.security.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;

import java.util.Collection;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.lucene.index.LeafReaderContext;
import org.apache.lucene.index.PostingsEnum;
import org.apache.lucene.index.Term;
import org.elasticsearch.common.settings.Settings;

import org.elasticsearch.plugins.Plugin;
import org.elasticsearch.plugins.ScriptPlugin;
import org.elasticsearch.script.SearchScript;
import org.elasticsearch.script.SearchScript.LeafFactory;
import org.elasticsearch.script.ScriptContext;
import org.elasticsearch.script.ScriptEngine;

import org.elasticsearch.index.fielddata.ScriptDocValues;
import org.elasticsearch.search.lookup.SearchLookup;
import org.elasticsearch.search.lookup.LeafSearchLookup;
import org.elasticsearch.search.lookup.LeafDocLookup;
import org.elasticsearch.search.lookup.SourceLookup;
import org.elasticsearch.SpecialPermission;

public class CosineScriptPlugin extends Plugin implements ScriptPlugin {
    private static final Logger logger = LogManager.getLogger(CosineScriptPlugin.class);

    @Override
    public ScriptEngine getScriptEngine(Settings settings, Collection<ScriptContext<?>> contexts) {
        return new MeedanScriptEngine();
    }

    // tag::meedan_engine
    private static class MeedanScriptEngine implements ScriptEngine {
        @Override
        public String getType() {
            return "meedan_scripts";
        }

        @Override
        public <T> T compile(String scriptName, String scriptSource,
                ScriptContext<T> context, Map<String, String> params) {
            if (context.equals(SearchScript.CONTEXT) == false) {
                throw new IllegalArgumentException(getType()
                        + " scripts cannot be used for context ["
                        + context.name + "]");
            }
            // we use the script "source" as the script identifier
            if ("cosine".equals(scriptSource)) {
                SearchScript.Factory factory = CosineLeafFactory::new;
                return context.factoryClazz.cast(factory);
            }
            throw new IllegalArgumentException("Unknown script name "
                    + scriptSource);
        }

        @Override
        public void close() {
            // optionally close resources
        }

        private static class CosineLeafFactory implements LeafFactory {
            private final Map<String, Object> params;
            private final SearchLookup lookup;
            private final List inputVector;

            private CosineLeafFactory(Map<String, Object> params, SearchLookup lookup) {
                if (params.containsKey("vector") == false) {
                    throw new IllegalArgumentException("Missing parameter [vector]");
                }
                this.params = params;
                this.lookup = lookup;
                this.inputVector = (List)params.get("vector");
            }

            @Override
            public boolean needs_score() {
                return false;  // Return true if the script needs the score
            }

            @Override
            public SearchScript newInstance(LeafReaderContext context) throws IOException {
                List inputVector = this.inputVector;

                return new SearchScript(params, lookup, context) {
                    public String convertToJson(List list) {
                      List<String> strings = new ArrayList<String>();
                      for (Object o : list) {
                        double d = (double)o;
                        strings.add(String.valueOf(d));
                      }
                      return "[" + String.join(",", strings) + "]";
                    }

                    public double getSimilarityFromAlegre(String vector1, String vector2) {
                      SecurityManager sm = System.getSecurityManager();
                      if (sm != null) {
                        sm.checkPermission(new SpecialPermission());
                      }
                      double similarity = AccessController.doPrivileged((PrivilegedAction<Double>)
                        () -> {
                          double value = 0.0d;
                          try {
                            String alegreUrl = System.getenv().get("ALEGRE_URL");
                            URL url = new URL(alegreUrl + "/text/wordvec/similarity");
                            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                            conn.setDoOutput(true);
                            conn.setRequestMethod("POST");
                            conn.setRequestProperty("Content-Type", "application/json");
                            String alegreAuth = System.getenv().get("ALEGRE_AUTH");
                            if (alegreAuth != null) {
                              String basicAuth = "Basic " + javax.xml.bind.DatatypeConverter.printBase64Binary(alegreAuth.getBytes());
                              conn.setRequestProperty("Authorization", basicAuth);
                            }
                            logger.info("Calling Alegre at " + alegreUrl + " with authentication " + alegreAuth);

                            String input = "{\"vector1\":\"" + vector1 + "\",\"vector2\":\"" + vector2 + "\"}";

                            OutputStream os = conn.getOutputStream();
                            os.write(input.getBytes());
                            os.flush();

                            BufferedReader br = new BufferedReader(new InputStreamReader((conn.getInputStream())));

                            String part;
                            String output = "";
                            while ((part = br.readLine()) != null) {
                              output += part;
                            }
                            conn.disconnect();
                            value = Double.parseDouble(output.replaceAll(".*:([0-9.]+).*", "$1"));
                          } catch (MalformedURLException e) {
                            logger.info("Exception when calling Alegre: " + e);
                          } catch (IOException e) {
                            logger.info("Exception when calling Alegre: " + e);
                          }
                          return value;
                        }
                      );
                      return similarity;
                    }

                    @Override
                    public double runAsDouble() {
                        double score = 0.0d;
                        try {
                          SourceLookup source = lookup.getLeafSearchLookup(context).source();
                          Object key = "vector";
                          Object vector = source.get(key);
                          List sourceVector = (List)vector;
                          String sourceVectorJSON = this.convertToJson(sourceVector);
                          String inputVectorJSON = this.convertToJson(inputVector);
                          score = this.getSimilarityFromAlegre(sourceVectorJSON, inputVectorJSON);
                        }
                        catch (Exception e) {
                          score = 0.0d;
                          logger.info("Exception: " + e);
                        }
                        return score;
                    }
                };
            }
        }
    }
    // end::meedan_engine
}
