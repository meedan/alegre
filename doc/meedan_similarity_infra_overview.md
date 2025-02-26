# Meedan Similarity Infrastructure Overview

This document and diagrams illustration the relationships between the parts of Meedan similarity services (Alegre) and the other Meedan systems it supports and depends on. the ‘nodes’ in this diagram  correspond to observable pieces of infrastructure. i.e. something we can go look at log files for when tracing through.

```mermaid
    graph LR
        Tipline_Queries --> Check_API
        Check_Web --> Alegre_Bot  --> Alegre_API_ECS_Service
        Rake_Tasks --> Check_API
        Check_API --> Check_Relationship_Store_Postgres_DB
        Check_API --> Alegre_API_ECS_Service
        Timpani --> Alegre_API_ECS_Service
        Alegre_API_ECS_Service --> Alegre_Postgres_DB
        Alegre_API_ECS_Service --> OpenSearch_Vector_Index
        Alegre_API_ECS_Service --> Redis_State_Cache

        Alegre_API_ECS_Service --> S3_TMK_Video_Fingerprint_Filestore
        subgraph Deprecated_Alegre_Text_Models
            Paraphrase_Multilingual
            Means_Tokens
            Indian_Sbert
        end
        Alegre_API_ECS_Service --> Deprecated_Alegre_Text_Models
        Alegre_API_ECS_Service --> Google_Lang_ID


        Alegre_API_ECS_Service --> Presto_API_Service
        Presto_API_Service --> Alegre_API_ECS_Service

        subgraph AWS_SQS_Queues
            Input_Queues
            Output_Queues
            DeadLetter_Queues
        end

        Presto_API_Service --> Input_Queues --> Presto_Models --> Output_Queues --> Presto_API_Service

        subgraph Presto_Models
            YAKE_Keywords_Model
            Paraphrase_Multilingual_Text_Model
            Indian_Sbert_Text_Model
            Means_Tokens_Text_Model
            Video_Model
            Audio_Model
            Image_Model
        end

        
        Video_Model --> S3_TMK_Video_Fingerprint_Filestore
        Audio_Model --> Alegre_Postgres_DB
        Image_Model --> Alegre_Postgres_DB

```

Questions:
* Does alegre bot go through Check API?


