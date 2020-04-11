This is a plugin for ElasticSearch. You can compile it with Maven and then install.

# Install

```
mvn clean install
/usr/share/elasticsearch/bin/elasticsearch-plugin install --verbose --batch file:///path/to/es-script-cosine-scoring/target/releases/meedan-cosine-0.0.1.zip
```

# Usage

After the plugin is installed, you're able to use the Meedan Cosine function for score calculation in your ES queries:

```
'function_score': {
    'functions': [
        {
            'script_score': {
                'script': {
                    'source': 'cosine',
                    'lang': 'meedan_scripts',
                    'params': {
                        'vector': <vector>
                        'model': <model>
                    }
                }
            }
        }
    ]
}
```
