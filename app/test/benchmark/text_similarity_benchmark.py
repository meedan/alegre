import argparse
import unittest
import json
import requests
import time
import os
import sys

from concurrent.futures import ThreadPoolExecutor
import faker


class AlegreTextSimilarityAPILoadTest(unittest.TestCase):
    """
    Load test Alegre text similarity endpoints for benchmark tests
    and debugging load failure states
    """

    LOCALES = ["es", "en_US", "zh_CN", "ja_JP", "pt", "or_IN", "hi_IN"]
    fake_content_source = faker.Faker(LOCALES)

    # http://alegre.qa but probably can only run when deployed
    # TODO: don't run this in live
    # ALEGRE_BASE_URL = "http://alegre:3100"
    # ALEGRE_BASE_URL = "http://localhost:3100"
    # ALEGRE_BASE_URL = "http://host.docker.internal:3100"
    ALEGRE_BASE_URL = os.getenv('ALEGRE_HOST', default="http://alegre:3100")
    MODEL_KEY = "paraphrase-multilingual-mpnet-base-v2"
    # MODEL_KEY = "elasticsearch"
    # MODEL_KEY = "openai-"

    def test_alegre_healthcheck(self):
        """
        Make sure the service is up and reachable
        """
        response = requests.get(self.ALEGRE_BASE_URL + "/healthcheck")
        assert response.ok is True, f"response was {response}"

    def test_alegre_text_similarity_old_api_contract(self):
        """
        Make sure text similarity endpoints exist and accept the arguments we need
        """
        # REQUEST VECTOR (corresponding to some text)
        # response = requests.get(
        #     self.ALEGRE_BASE_URL + "/text/similarity/",
        #     params=json.dumps(
        #         {
        #             "text": sample_text,
        #             # 'threshold': 0.0   <-- TODO: do we need this?
        #         }
        #     ),
        # )
        # assert response.ok is True, f"response was {response}"
        # result = json.loads(response.text)
        # print(f"vector request result was {result}")
        # TODO: assert that we got back a vector in the response

        # TODO: new sync and async endpoints 

        # STORE A VECTOR (corresponding to some text)
        # OR modify alegre with a flag that can return the vector.
        sample_text = "This is some example text in English that we want to vectorize and store"
        sample_content_item_id = "item_99"
        example = {
            "text": sample_text,
            "doc_id": sample_content_item_id,
            "context": {"type": "alegre_test_content_item_text"},
            "models": [self.MODEL_KEY],  # model must be included
        }
        response = requests.post(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps(example),
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f"post response was {response.text}"
        result = json.loads(response.text)
        # print(f"store vector post result was {result}")

        # NOTE: need delay between storing vector and querying
        time.sleep(5)

        # QUERY A VECTOR (get the closest doc id corresponding to some text)
        response = requests.post(
            self.ALEGRE_BASE_URL + "/text/similarity/search/",
            json={
                "text": sample_text,
                "context": {"type": "alegre_test_content_item_text"},
                "models": [self.MODEL_KEY],  # model must be included
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f"get response was {response}"
        result = json.loads(response.text)
        # print(f"query result was {result}")
        # check asssert that result matches sample_content_item_id
        assert result["result"][0]["id"] == sample_content_item_id

        # DELETE A VECTOR (corresponding to the text of a content item)
        response = requests.delete(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps(
                {
                    "doc_id": sample_content_item_id,
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f" delete response was {response} : {response.text}"

        # TODO: UPDATE A VECTOR

    def test_many_vector_stores_non_parallel_old(self, num_saves=100):
        """
        write a many vectors as quickly as possible from a single thread (old endpoint)
        """
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "alegre_test_content_item_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        start_time = time.time()
        for doc in documents:
            response = requests.post(
                self.ALEGRE_BASE_URL + "/text/similarity/",
                data=json.dumps(doc),
                headers={"Content-Type": "application/json"},
            )
            assert response.ok is True
        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"submitted {num_saves} vectorization requests to /text/similarity/ in {duration} seconds. rate= {submit_rate}"
        )

        # August, 2023
        # on localhost I'm seeing submitted 999 vectorization requests in 17.251052141189575 seconds.
        # rate= 0.017268320461651228 items/sec
        # using that as benchmark for now 20 sec for 1k items
        # assert submit_rate < 0.02

        # lets time the queries
        start_time = time.time()
        for doc in documents:
            response = requests.post(
                self.ALEGRE_BASE_URL + "/text/similarity/search/",
                json={
                    "text": doc["text"],
                    "context": doc["context"],
                    "model": self.MODEL_KEY,  # model must be included
                    "threshold": 0.0,  # return all results
                },
                headers={"Content-Type": "application/json"},
            )
            assert response.ok is True, f"response was {response}"
            assert json.loads(response.text)["result"][0]["id"] == doc["doc_id"], f'response was {response.text}'

        end_time = time.time()
        duration = end_time - start_time
        query_rate = duration / num_saves
        print(
            f"queried {num_saves} search requests in {duration} seconds. rate= {query_rate}"
        )
        # August 2024
        # on localhost  queried 1000 search requests in 6.885326147079468 seconds. rate= 0.006885326147079468
        # Feb 2025 queried 100 search requests in 58.578511238098145 seconds. rate= 0.5857851123809814
        # assert query_rate < 0.02

        # time the deletes
        start_time = time.time()
        for doc in documents:
            response = requests.delete(
                self.ALEGRE_BASE_URL + "/text/similarity/",
                data=json.dumps({"doc_id": doc["doc_id"]}),
                headers={"Content-Type": "application/json"},
            )
        assert response.ok is True, f" delete response was {response} : {response.text}"

        end_time = time.time()
        duration = end_time - start_time
        delete_rate = duration / num_saves
        print(
            f"sent {num_saves} delete requests in {duration} seconds. rate= {delete_rate}"
        )
        # August, 2023
        # on localhost sent deleted 1000 delete requests in 12.588739156723022 seconds. rate= 0.012588739156723023
        # Feb 2025
        # sent 100 delete requests in 2.6708664894104004 seconds. rate= 0.026708664894104003
        # assert delete_rate < 0.02

    def test_many_vector_stores_non_parallel_sync(self, num_saves=100):
        """
        write a many vectors as quickly as possible from a single thread (new sync endpoint)
        """
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "alegre_test_sync_content_item_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        start_time = time.time()
        for doc in documents:
            response = requests.post(
                self.ALEGRE_BASE_URL + "/similarity/sync/text",
                data=json.dumps(doc),
                headers={"Content-Type": "application/json"},
            )
            assert response.ok is True
        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"submitted {num_saves} vectorization requests to /similarity/sync/text in {duration} seconds. rate= {submit_rate}"
        )

    def test_many_vector_stores_non_parallel_async(self, num_saves=100):
        """
        write a many vectors as quickly as possible from a single thread (new _async_ endpoint)
        """
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "alegre_test_async_content_item_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        start_time = time.time()
        for doc in documents:
            response = requests.post(
                self.ALEGRE_BASE_URL + "/similarity/async/text",
                data=json.dumps(doc),
                headers={"Content-Type": "application/json"},
            )
            assert response.ok is True
        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"submitted {num_saves} vectorization requests to /similarity/async/text in {duration} seconds. rate= {submit_rate}"
        )

    def _store_doc_to_alegre_old(self, doc):
        response = requests.post(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps(doc),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test old",  
            },
        )
        assert response.ok is True

    def _store_doc_to_alegre_sync(self, doc):
        response = requests.post(
            self.ALEGRE_BASE_URL + "/similarity/sync/text",
            data=json.dumps(doc),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test sync",  
            },
        )
        assert response.ok is True

    def _store_doc_to_alegre_async(self, doc):
        response = requests.post(
            self.ALEGRE_BASE_URL + "/similarity/async/text",
            data=json.dumps(doc),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test async",  
            },
        )
        assert response.ok is True

    def _query_doc_from_alegre(self, doc):
        response = requests.post(
            self.ALEGRE_BASE_URL + "/text/similarity/search/",
            json={
                "text": doc["text"],
                "context": doc["context"],
                "model": self.MODEL_KEY,  # model must be included
                "threshold": 0.0,  # return all results
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test",  # TODO: cfg should know version
            },
        )
        assert response.ok is True, f"response was {response}"
        # confirm correct doc returned
        assert json.loads(response.text)["result"][0]["id"] == doc["doc_id"], f'response was {response.text}'

    def _query_doc_from_alegre_sync(self, doc):
        response = requests.post(
            self.ALEGRE_BASE_URL + "/similarity/sync/text",
            json={
                "text": doc["text"],
                "context": doc["context"],
                "model": self.MODEL_KEY,  # model must be included
                "threshold": 0.0,  # return all results
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test",  # TODO: cfg should know version
            },
        )
        assert response.ok is True, f"response was {response}"
        # confirm correct doc returned
        assert json.loads(response.text)["result"][0]["id"] == doc["doc_id"], f'response was {response.text}'

    def _delete_doc_from_alegre(self, doc):
        # DELETE A VECTOR (corresponding to the text of a content item)
        response = requests.delete(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps({"doc_id": doc["doc_id"]}),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Alegre Load Test",  # TODO: cfg should know version
            },
        )
        assert response.ok is True, f" delete response was {response} : {response.text}"

    def test_many_vector_stores_semi_parallel_old(
        self, num_saves=10, thread_pool_size=10
    ):
        """
        write a whole bunch of vectors as quickly as possible
        from a single thread
        """
        
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "alegre_test_parallel_old_item_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        start_time = time.time()
        pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        # store vectors and block (we hope) until all done
        pool.map(self._store_doc_to_alegre_old, documents)

        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"Old endpoint submitted {num_saves} batch parallelized vectorization requests in {duration} seconds. rate= {submit_rate}"
        )

        # query vector
        start_time = time.time()
        pool.map(self._query_doc_from_alegre, documents)
        end_time = time.time()
        duration = end_time - start_time
        query_rate = duration / num_saves
        print(
            f"Old endpoint submitted {num_saves} batch parallelized query requests in {duration} seconds. rate= {query_rate}"
        )

        # delete vector
        start_time = time.time()
        pool.map(self._delete_doc_from_alegre, documents)
        end_time = time.time()
        duration = end_time - start_time
        delete_rate = duration / num_saves
        print(
            f"old endpoint submitted {num_saves} batch parallelized delete requests in {duration} seconds. rate= {delete_rate}"
        )

        # August, 2023
        # NOTE: for 10k items on localhost elastic submits are completing in ~18 seconds,
        # but it is taking ~20min check-alegre logs to finish processing! ~ 10/sec
        # for *1k* items on localhost meanstokesn, submits are ~ 263 seconds and, alegre logs tak ~20min
        # ... so 10X slower at ~ 1/sec

    def test_many_vector_stores_semi_parallel_sync(
        self, num_saves=10, thread_pool_size=10
    ):
        """
        write a whole bunch of vectors as quickly as possible
        from a single thread using the new sync (blocking) route
        """
        
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "alegre_parallel_sync_test_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        start_time = time.time()
        pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        # store vector
        pool.map(self._store_doc_to_alegre_sync, documents)
        # NOTE: I'm not very confidant that pool.map is actually blocking
        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"New sync endpoint submitted {num_saves} batch parallelized vectorization requests in {duration} seconds. rate= {submit_rate}"
        )

        # query vector
        start_time = time.time()
        pool.map(self._query_doc_from_alegre_sync, documents)
        end_time = time.time()
        duration = end_time - start_time
        query_rate = duration / num_saves
        print(
            f"submitted {num_saves} batch parallelized query requests in {duration} seconds. rate= {query_rate}"
        )

        # delete vector
        start_time = time.time()
        pool.map(self._delete_doc_from_alegre, documents)
        end_time = time.time()
        duration = end_time - start_time
        delete_rate = duration / num_saves
        print(
            f"submitted {num_saves} batch parallelized delete requests in {duration} seconds. rate= {delete_rate}"
        )


if __name__ == "__main__":
    environment = os.getenv("DEPLOY_ENV", "local")
    # don't run in live because can generate a lot of traffic and disrupt infrastructure
    assert (environment != 'live'), "Benchmark script cannot  run in live environment"
    unittest.main()