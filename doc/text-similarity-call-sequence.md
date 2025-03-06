# Sequence diagram for text similarity calls [DRAFT]

There are multiple paths

* Text similarity via old (blocking) endpoint
* Text similarity via the 'sync' (blocking) endpoint
* Text similairty via the 'async' endpoint



## /similarity/sync/text 

 This diagram traces blocking  'sync' text similarity call from Check API, starting from `similarity_sync_controller.py`.  When a text item is sent, the request is held open, blocking on a redis Key, until the vector response from Presto unblocks the key. The vector from the text model is then stored in the appropriate OpenSearch index seperately for each model.  Alegre then queries to look up similar items via ES text indicies and vector cosine similarity for the just-submitted item, responding to CheckAPI with any items it finds. 

Note: When there are multiple text models for various language-specific indexes, Alegre queries each one in sequence (not in parallel)

TODO: when unpacking the presto callback loop, how do we know all keys have been recieved to respond to Check

TODO: language lookups

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

    loop for each model type
        Alegre Service->>Presto API: /process_item/{model_key} item1:'example text'
        activate Presto API
        Presto API->>Alegre Service: request recieved 
        deactivate Presto API
    Alegre Service-)Redis: waiting for 'text_item1':
    deactivate Alegre Service
    end
    
    activate Redis

    activate Presto API
    Presto API-->>Presto API: communicate with text model via SQS queues
    
    loop for each model type
        Presto API->>Alegre Service: /presto/receive/add_item/ item1: <vector> 
        activate Alegre Service

        Alegre Service->>+Presto API: item1 updated
        deactivate Presto API
        
        Alegre Service-)Redis: push 'text_item1':
        deactivate Alegre Service
        deactivate Redis
    end

    Note over Alegre Service: when all (or any?) redis key unblocked or timed out
    activate Alegre Service
    
    loop for each model type
        activate OpenSearch
        Alegre Service->>OpenSearch: store item1: <vector>
        OpenSearch->>Alegre Service: ok
        deactivate OpenSearch
    end

    loop for each model type
        activate OpenSearch
        Alegre Service->>OpenSearch: search item1: <vector>
        OpenSearch->>Alegre Service: similar results [item1, item2]
        deactivate OpenSearch
    end

    Note over Alegre Service: collect results from all models

    deactivate Alegre Service
    Alegre Service-->>Check API: found similar: [item1, item2]
    deactivate Check API

```

## /similarity/async/text 

This diagram traces the async (non-blocking) text similarity calls, starting from `similarity_sync_controller.py`.  First stores the object with out the vector?, just context (for ES text index?)  

Note: Behavior is modified by `suppress_response` (default False) and `requires_callback` (default True) arguments in call

Note: The lookup OpenAI embeddings with a redis cache is conditional on OpenAI model key, but still seems to execute after presto callback from other model?

TODO: does CheckAPI have to track state callback for each model
TODO: what is the final cache of results in redis for?

DRAFT (this needs another pass through to confirm it is correct)
```mermaid
sequenceDiagram
    participant Check API
    participant Alegre Service
    participant OpenSearch
    participant Redis
    participant Presto API
    participant OpenAI API

    box Alegre
    participant Alegre Service
    participant OpenSearch
    participant Redis
    end
    
    activate Check API
    Check API-->>Alegre Service: /similarity/async/text item1:'example text'
    activate Alegre Service

    Alegre Service ->> OpenSearch: store item1:'example text'
    OpenSearch ->> Alegre Service: ok

    loop for each model type
        Alegre Service->>Presto API: /process_item/{model_key} item1:'example text'
        activate Presto API
        Presto API->>Alegre Service: request recieved 
        deactivate Presto API
    deactivate Alegre Service
    end
    
  

    activate Presto API
    Presto API-->>Presto API: communicate with text model via SQS queues
    
    loop for each model type
        Presto API->>Alegre Service: /presto/receive/add_item/ item1: <vector> 
        activate Alegre Service
        
        Alegre Service->>OpenSearch: get item1
        OpenSearch->>Alegre Service: item1

        
        Alegre Service->>OpenSearch: store item1: <vector>
        activate OpenSearch
        OpenSearch->>Alegre Service: ok
        deactivate OpenSearch

        Note right of Alegre Service: OpenAI lookup conditional on model key
        Alegre Service->> Redis: check if OpenAI item1 vector already cached?
        Redis->>Alegre Service: (optionally) cached <vector>
        Alegre Service->> OpenAI API: get vector for 'example text'
        OpenAI API->>Alegre Service: <vector>
        Alegre Service->> Redis: cache OpenAI vector item1:<vector>

        activate OpenSearch
        Alegre Service->>OpenSearch: search item1: <vector>
        OpenSearch->>Alegre Service: similar results [item1, item2]
        deactivate OpenSearch
        Alegre Service->>Check API: found similar: [item1, item2]
        Alegre Service->>Redis: cache model, item1: results 

        Alegre Service->>Presto API: item1 results
        deactivate Presto API

        deactivate Alegre Service


    end




    deactivate Check API

```
