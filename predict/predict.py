import os
from haystack.pipelines import Pipeline
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.nodes import BM25Retriever, PromptNode, PromptModel
from fastrag.rankers.colbert import ColBERTRanker
import http.client
import json
from haystack.nodes import BM25Retriever, SentenceTransformersRanker, PromptTemplate
from transformers import AutoTokenizer
import requests
import time

class main_endpoint:
    def __init__(self):
        self.cnvrg = True
        
    def read_environ_variables(self):
        # pipeline varirables
        # print(os.environ)
        self.provider = os.environ["PROVIDER"]
        self.host = os.environ["ELASTIC_HOST"]
        self.port = os.environ["ELASTIC_PORT"]
        self.username = os.environ["ELASTIC_USERNAME"]
        self.password = os.environ["ELASTIC_PASSWORD"]
        self.index = os.environ["ELASTIC_INDEX"]
        self.search_fields = "content"
        self.retrieverk = os.environ["RETRIEVER_N"]
        self.rankerk = os.environ["RANKER_N"]
        self.model_name = self.check_variable("MODEL_NAME")
        
        # llm variables
        self.api_key = os.environ["LLM_API_KEY"]

        if self.provider.lower() != "cnvrg":
            self.cnvrg = False
            
        # Azure support will be added in the next release
        # self.deployment_name = self.check_variable("AZURE_DEPLOYMENT_NAME")
        # self.base_url = self.check_variable("AZURE_BASE_URL")

        # setup cnvrg credentials
        
        if self.provider == "cnvrg":
            self.cnvrg_url = os.environ["URL"]
            self.cnvrg_1 = self.cnvrg_url[
                len("https://") : self.cnvrg_url.rfind("cnvrg.io") + len("cnvrg.io")
            ]
            self.cnvrg_2 = self.cnvrg_url[
                self.cnvrg_url.rfind("cnvrg.io") + len("cnvrg.io") :
            ]

        # define the prompt text
        self.prompt_text = self.check_variable("PROMPT")

    def check_variable(self, variable):
        try:
            return os.environ[variable]
        except KeyError:
            return None

    def RAG_pipeline(self):
        self.scheme = self.check_variable("SCHEME")

        document_store = ElasticsearchDocumentStore(
            host=self.host,
            port=self.port,
            index=self.index,
            username = self.username,
            password = self.password,
            search_fields=[self.search_fields],
            refresh_type="false",
            timeout = 30,
            scheme = self.scheme
        )
        retriever = BM25Retriever(
            document_store=document_store, top_k=int(self.retrieverk)
        )
        ranker = ColBERTRanker(checkpoint_path="Intel/ColBERT-NQ", top_k=int(self.rankerk))
        # ranker = SentenceTransformersRanker(
        #     model_name_or_path="cross-encoder/ms-marco-MiniLM-L-6-v2",
        #     top_k=5,
        #     batch_size=32,
        #     use_gpu=False,
        # )
        self.pipeline = Pipeline()
        self.pipeline.add_node(component=retriever, name="Retriever", inputs=["Query"])
        self.pipeline.add_node(component=ranker, name="Reranker", inputs=["Retriever"])

    def huggingface_query(self, text):
        encoded = self.tk.encode(text)
        limited = encoded[:self.tk.model_max_length]
        decoded = self.tk.decode(limited, skip_special_tokens=True)

        output = {
            "inputs": decoded,
            "parameters": {"max_new_tokens": self.tk.model_max_length},
        }
        response = requests.post(self.API_URL, headers=self.headers, json=output)
        return response.json()

    def external_language_model(self):

        if self.provider.lower() == "openai":
            # model = PromptModel(self.model_name, api_key=self.api_key)
            self.LLM = PromptNode(self.model_name, api_key=self.api_key)
            self.cnvrg = False

        elif self.provider.lower() == "huggingface":
            os.environ["HUGGINGFACEHUB_API_TOKEN"] = self.api_key

            self.tk = AutoTokenizer.from_pretrained(self.model_name)
            self.API_URL = (
                f"https://api-inference.huggingface.co/models/{self.model_name}"
            )
            self.headers = {"Authorization": f"Bearer {self.api_key}"}

            self.LLM = self.huggingface_query

        else:
            raise Exception(
                "Please provide a valid LLM service provider in the environment variable PROVIDER, acceptable ones are cnvrg, openai, huggingface"
            )
        # Azure support will be added in the next release
        # if self.deployment_name is not None:
        #     model = PromptModel(
        #         model_name_or_path=self.model_name,
        #         api_key=self.api_key,
        #         model_kwargs={
        #             "azure_deployment_name": self.deployment_name,
        #             "azure_base_url": self.base_url,
        #         },
        #     )
        #     self.LLM = PromptNode(model)
        
    def cnvrg_language_model(self, data):
        conn = http.client.HTTPSConnection(self.cnvrg_1, 443)
        headers = {"Cnvrg-Api-Key": self.api_key, "Content-Type": "application/json"}
        request_dict = {"prompt": data}
        payload = '{"input_params":' + json.dumps(request_dict) + "}"
        conn.request("POST", self.cnvrg_2, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def call_llm(self, data,):
        if self.cnvrg:
            return self.cnvrg_language_model(data)
        else:
            return self.LLM(data)

# print('455')
definitions = main_endpoint()
definitions.read_environ_variables()
start = time.time()
definitions.RAG_pipeline()
end = time.time()
print(end - start)
if definitions.cnvrg == False:
    definitions.external_language_model()


def prepare_prompt(prompt, documents, query):
    # replace documents
    prompt = prompt.replace("{documents}", documents)
    # replace query
    prompt = prompt.replace("{query}", query)
    return prompt


def preprocess(result, definitions):
    query = result["query"]
    documents = [
        result["documents"][i].content for i in range(0, len(result["documents"]))
    ]
    documents = " ".join(documents)
    return prepare_prompt(definitions.prompt_text, documents, query)

def query(data):
    params = {}
    query = data['query']
    result = definitions.pipeline.run(query=query, params=params, debug=False)
    preprocessed = preprocess(result, definitions)
    print(preprocessed)
    answer = definitions.call_llm(preprocessed)
    return answer
