import unittest
import yaml
import os
from updator_minio import minio_updator

class Test_main(unittest.TestCase):
    """Defining the sample data and files to carry out the testing"""

    def setUp(self):
        #read the arguments and pass them to the minioupdator
        with open("test_minio.yaml","r") as f:
            data_loaded = yaml.safe_load(f)

        self.data = data_loaded
        self.object = minio_updator(data_loaded)
        
            
class Test_minio(Test_main):
    
    def test_a_get_documents(self):
        result = self.object.get_documents(self.data["document_name"])
        self.assertEqual(result, self.data["document_name"])

    def test_b_updator(self):
        result = self.object.updator(self.data["document_name"])
        self.assertEqual(result, "updated")
        
    def test_c_deletor(self):
        result = self.object.deletor(self.data["document_name"])
        self.assertEqual(result, "deleted")

    def test_d_process(self):
        result = self.object.process([{"eventName": "s3:ObjectCreated:Put","s3":{"object":{"key":self.data["document_name"]}}} ])
        self.assertEqual(result, "processed")



            
        
if __name__ == "__main__":
    unittest.main()
