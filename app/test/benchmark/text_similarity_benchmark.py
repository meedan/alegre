import unittest
import json
import requests
import time
import os

from concurrent.futures import ThreadPoolExecutor
import faker


class AlegreTextAPILoadTest(unittest.TestCase):
    """
    Not sure where this test belongs. Should not be part of
    normal CI and unit tests. Goal is to test API limits
    of functionality in Alegre that Timpani will need.
    """

    LOCALES = ["es", "en_US", "zh_CN", "ja_JP", "pt", "or_IN", "hi_IN"]
    fake_content_source = faker.Faker(LOCALES)

    # TODO: this is for local, need to change for QA
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
        sample_timpani_content_item_id = "item_99"
        example = {
            "text": sample_text,
            "doc_id": sample_timpani_content_item_id,
            "context": {"type": "timpani_content_item_text"},
            "models": [self.MODEL_KEY],  # model must be included
        }
        response = requests.post(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps(example),
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f"post response was {response.text}"
        result = json.loads(response.text)
        print(f"store vector post result was {result}")

        # NOTE: need delay between storing vector and querying
        time.sleep(5)

        # QUERY A VECTOR (get the closest doc id corresponding to some text)
        response = requests.get(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            json={
                "text": sample_text,
                "context": {"type": "timpani_content_item_text"},
                "models": [self.MODEL_KEY],  # model must be included
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f"get response was {response}"
        result = json.loads(response.text)
        print(f"query result was {result}")
        # check asssert that result matches sample_timpani_content_item_id
        assert result["result"][0]["id"] == sample_timpani_content_item_id

        # DELETE A VECTOR (corresponding to the text of a content item)
        response = requests.delete(
            self.ALEGRE_BASE_URL + "/text/similarity/",
            data=json.dumps(
                {
                    "doc_id": sample_timpani_content_item_id,
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        assert response.ok is True, f" delete response was {response} : {response.text}"

        # TODO: UPDATE A VECTOR

    def test_many_vector_stores_non_parallel_old(self, num_saves=100):
        """
        write a many vectors as quickly as possiblefrom a single thread
        """
        documents = []
        # make the documents
        for n in range(num_saves):
            doc = {
                "text": self.fake_content_source.text(),
                "doc_id": f"test_doc_{n}",
                "context": {"type": "timpani_content_item_text"},
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
            f"submitted {num_saves} vectorization requests in {duration} seconds. rate= {submit_rate}"
        )

        # August, 2023
        # on localhost I'm seeing submitted 999 vectorization requests in 17.251052141189575 seconds.
        # rate= 0.017268320461651228 items/sec
        # using that as benchmark for now 20 sec for 1k items
        assert submit_rate < 0.02

        # lets time the queries
        start_time = time.time()
        for doc in documents:
            response = requests.get(
                self.ALEGRE_BASE_URL + "/text/similarity/",
                json={
                    "text": doc["text"],
                    "context": doc["context"],
                    "model": self.MODEL_KEY,  # model must be included
                    "threshold": 0.0,  # return all results
                },
                headers={"Content-Type": "application/json"},
            )
            assert response.ok is True, f"response was {response}"
            assert json.loads(response.text)["result"][0]["id"] == doc["doc_id"]

        end_time = time.time()
        duration = end_time - start_time
        query_rate = duration / num_saves
        print(
            f"queried {num_saves} search requests in {duration} seconds. rate= {query_rate}"
        )
        # on localhost  queried 1000 search requests in 6.885326147079468 seconds. rate= 0.006885326147079468
        assert query_rate < 0.02

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
        assert delete_rate < 0.02

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
        response = requests.get(
            self.ALEGRE_BASE_URL + "/text/similarity/",
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
        assert json.loads(response.text)["result"][0]["id"] == doc["doc_id"]

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
        self, num_saves=1000, thread_pool_size=100
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
                "context": {"type": "timpani_content_item_text"},
                "model": self.MODEL_KEY,  # model must be included
            }
            documents.append(doc)

        pool = ThreadPoolExecutor(max_workers=thread_pool_size)

        # store vector
        start_time = time.time()
        pool.map(self._store_doc_to_alegre_old, documents)
        end_time = time.time()
        duration = end_time - start_time
        submit_rate = duration / num_saves
        print(
            f"submitted {num_saves} batch parallelized vectorization requests in {duration} seconds. rate= {submit_rate}"
        )

        # query vector
        start_time = time.time()
        pool.map(self._query_doc_from_alegre, documents)
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

        # August, 2023
        # NOTE: for 10k items on localhost elastic submits are completing in ~18 seconds,
        # but it is taking ~20min check-alegre logs to finish processing! ~ 10/sec
        # for *1k* items on localhost meanstokesn, submits are ~ 263 seconds and, alegre logs tak ~20min
        # ... so 10X slower at ~ 1/sec


if __name__ == "__main__":
    unittest.main()