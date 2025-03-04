# Sequence diagram for text similarity calls

There are multiple paths

* Text similarity via old (blocking) endpoint
* Text similarity via the 'sync' (blocking) endpoint
* Text similairty via the 'async' endpoint



## /similarity/sync/text 

This diagram traces blocking  'sync' text similarity call from Check API.  When a text item is sent, the request is held open, blocking on a redis Key, until the vector response from Presto unblocks the key. The vector from the text model is then stored in the appropriate OpenSearch index seperately for each model.  Alegre then queries to look up similar items via ES text indicies and vector cosine similarity for the just-submitted item, responding to CheckAPI with any items it finds. 

Note: When there are multiple text models for various language-specific indexes, Alegre queries each one in sequence (not in parallel)

```mermaid
sequenceDiagram
    participant Check API
    participant Alegre Service
    participant OpenSearch
    participant Redis
    participant Presto API

    

    box Alegre
    participant Alegre Service
    participant OpenSearch
    participant Redis
    end
    
    activate Check API
    Check API-->>Alegre Service: /similarity/sync/text item1:'example text'
    activate Alegre Service

    
    Alegre Service-->>Presto API: item1:'example text'
    activate Presto API
    Presto API-->>Alegre Service: request recieved 
    deactivate Presto API

    
    Alegre Service--)Redis: waiting for 'text_item1':
    deactivate Alegre Service
    activate Redis

    activate Presto API
    Presto API-->>Presto API: communicate with model via SQS queues
    
    
    Presto API-->>Alegre Service: /presto/receive/add_item/ item1: <vector> 
    activate Alegre Service

    Alegre Service-->>+Presto API: item1 updated
    deactivate Presto API
    Alegre Service--)Redis: push 'text_item1':
    
    deactivate Redis


    activate OpenSearch
    Alegre Service-->>OpenSearch: store item1: <vector>
    OpenSearch-->>Alegre Service: ok
    deactivate OpenSearch

    activate OpenSearch
    Alegre Service-->>OpenSearch: search item1: <vector>
    OpenSearch-->>Alegre Service: similar results [item1, item2]
    deactivate OpenSearch

    deactivate Alegre Service
    Alegre Service-->>Check API: found similar: [item1, item2]
    deactivate Check API

```