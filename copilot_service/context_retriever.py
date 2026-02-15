from elasticsearch import Elasticsearch
from config import ES_HOST, ES_INDEX, MAX_CONTEXT_RESULTS

es = Elasticsearch(ES_HOST)

def retrieve_context(question: str):

    query = {
        "query": {
            "multi_match": {
                "query": question,
                "fields": [
                    "zone",
                    "description",
                    "verdict"
                ]
            }
        },
        "size": MAX_CONTEXT_RESULTS,
        "sort": [{"timestamp": "asc"}]
    }

    response = es.search(index=ES_INDEX, body=query)

    return [hit["_source"] for hit in response["hits"]["hits"]]
