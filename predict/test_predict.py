import unittest
from predictblue import main_endpoint, prepare_prompt, query
import yaml
import os

class Test_main(unittest.TestCase):
    """Defining the sample data and files to carry out the testing"""

    def setUp(self):
        with open("test_predict.yaml","r") as f:
            data_loaded = yaml.safe_load(f)
        self.object = main_endpoint
        
        os.environ["prompt"] = data_loaded["prompt"]
        os.environ["documents"] =data_loaded["documents"]
        os.environ["query"] =data_loaded["query"]
        os.environ["final_prompt"]= data_loaded["final_prompt"]
        os.environ["test_cnvrg_llm"] =data_loaded["test_cnvrg_llm"]
        os.environ["test_huggingface"] = data_loaded["test_huggingface"]
        os.environ["provider"] = data_loaded["provider"]
        os.environ["PORT"] = data_loaded["port"]
        os.environ["HOST"] = data_loaded["host"]
        os.environ["INDEX"] = data_loaded["index"] 
        os.environ["RETRIEVER_N"] = data_loaded["retriever_n"]
        os.environ["RANKER_N"] = data_loaded["ranker_n"]

        self.object.read_environ_variables()
        
class Test_predict(Test_main):

    def prepare_prompt(self): 
        result = prepare_prompt(self.prompt,self.documents,self.query)
        self.assertEqual(result, self.final_prompt)

    def test_cnvrg_language_model(self):
        if(self.test_cnvrg_llm == True):
            result = main_endpoint.cnvrg_language_model(self.final_prompt)
            self.assertIsInstance(result, dict)
        else:
            raise unittest.SkipTest('Cnvrg LLM not tested.')
    def test_RAG_pipeline(self):
        if(self.test_rag ==True):
            self.object.RAG_pipeline()
        else:
            raise unittest.SkipTest('ElasticSearch connection not tested.')

    def test_huggingface(self):
        if(self.provider == "huggingface"):
            self.object.external_language_model()
            result = self.object.huggingface_query(self.final_prompt)
            self.assertIsInstance(result, dict)
        else:
            raise unittest.SkipTest('huggingface llm not tested.')

    def test_openai(self):
        if(self.provider == "openai"):
            self.object.external_language_model()
            result = self.object.call_llm(self.final_prompt)
            self.assertIsInstance(result, dict)
        else:
            raise unittest.SkipTest('openai llm not tested.')

    def test_full(self):
        if(self.provider is not None and self.test_rag ==True):
            result = query(self.query)
            self.assertIsInstance(result, dict)
        else:
            raise unittest.SkipTest('Full pipeline not tested.')

            
        
if __name__ == "__main__":
    unittest.main()
