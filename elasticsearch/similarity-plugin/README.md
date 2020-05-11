This is a plugin for ElasticSearch. You can compile it with Maven and then install.

# Install

```
mvn clean install
/usr/share/elasticsearch/bin/elasticsearch-plugin install --verbose --batch file:///path/to/similarity/target/releases/similarity-1.0.0.zip
```

# Usage

After the plugin is installed, you're able to use the Meedan Similarity function for score calculation in your ES queries:

```
'function_score': {
    'functions': [
        {
            'script_score': {
                'script': {
                    'source': 'similarity',
                    'lang': 'meedan_scripts',
                    'params': {
                        'vector': <vector>
                    }
                }
            }
        }
    ]
}
```
