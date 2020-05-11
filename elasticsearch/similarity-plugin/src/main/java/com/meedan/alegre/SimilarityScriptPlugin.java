package com.meedan.alegre;

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
import org.elasticsearch.script.ScoreScript;
import org.elasticsearch.script.ScoreScript.LeafFactory;
import org.elasticsearch.script.ScriptContext;
import org.elasticsearch.script.ScriptEngine;

import org.elasticsearch.index.fielddata.ScriptDocValues;
import org.elasticsearch.search.lookup.SearchLookup;
import org.elasticsearch.search.lookup.LeafSearchLookup;
import org.elasticsearch.search.lookup.LeafDocLookup;
import org.elasticsearch.search.lookup.SourceLookup;
import org.elasticsearch.SpecialPermission;

import mikera.vectorz.Vector;

public class SimilarityScriptPlugin extends Plugin implements ScriptPlugin {
    private static final Logger logger = LogManager.getLogger(SimilarityScriptPlugin.class);

    @Override
    public ScriptEngine getScriptEngine(Settings settings, Collection<ScriptContext<?>> contexts) {
        return new SimilarityScriptEngine();
    }

    // tag::meedan_engine
    private static class SimilarityScriptEngine implements ScriptEngine {
        @Override
        public String getType() {
            return "meedan_scripts";
        }

        @Override
        public <T> T compile(String scriptName, String scriptSource,
                ScriptContext<T> context, Map<String, String> params) {
            if (context.equals(ScoreScript.CONTEXT) == false) {
                throw new IllegalArgumentException(getType()
                        + " scripts cannot be used for context ["
                        + context.name + "]");
            }
            // we use the script "source" as the script identifier
            if ("similarity".equals(scriptSource)) {
                ScoreScript.Factory factory = SimilarityLeafFactory::new;
                return context.factoryClazz.cast(factory);
            }
            throw new IllegalArgumentException("Unknown script name "
                    + scriptSource);
        }

        @Override
        public void close() {
            // optionally close resources
        }

        private static class SimilarityLeafFactory implements LeafFactory {
            private final Map<String, Object> params;
            private final SearchLookup lookup;
            private final List inputVector;

            private SimilarityLeafFactory(Map<String, Object> params, SearchLookup lookup) {
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
            public ScoreScript newInstance(LeafReaderContext context) throws IOException {
                List inputVector = this.inputVector;

                return new ScoreScript(params, lookup, context) {
                    @Override
                    public double execute() {
                        double score = 0.0d;
                        try {
                          SourceLookup source = lookup.getLeafSearchLookup(context).source();
                          Object key = "vector";
                          Object vector = source.get(key);
                          List sourceVector = (List)vector;
                          Vector v1 = Vector.create(inputVector);
                          Vector v2 = Vector.create(sourceVector);
                          score = 1.0 - v1.angle(v2) / Math.PI;
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
