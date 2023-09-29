import os
import argparse
import traceback
import dash
from haystack.document_stores import ElasticsearchDocumentStore
from haystack import Document
from minio import Minio
import json
import time
import logging
from io import StringIO
from dash_extensions.enrich import Output, Input, html, dcc
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

class minio_updator:
    def __init__(self):
        self.bucket_name = 'harshul-kafka'
        self.logger = logging
        # try:
        #     args["username"]
        # except:
        #     args["username"]=None
        # try:
        #     args["password"]
        # except:
        #     args["password"]=None
        # define document store resource
        self.document_store = ElasticsearchDocumentStore(
            host='10.42.6.227',
            port='9200',
            index='demo',
            search_fields=["content"],
            refresh_type="false",
        )

        self.logger.info("Connected to Elastic Search \u2705")

        # define MinIO client
        self.client = Minio(
            'minio-standalone.aks-cicd-19635.cicd.cnvrg.me',
            access_key='Q824h9vGSDFG74gj94MKCOS84V0a7f2a0fnZa',
            secret_key='WZHu00yVPQNiGIs104ZIHprWx5Qgvog23EzPIs2x6qQvBdpKoo2EMkg2EzmHhb1BUvtFpKTdAKD9r4uI7xR',
            secure=False,
        )
        self.logger.info("MinIO client connected \u2705")
        

    def listener(self):
        """
        Add code for conitnous listening to event notifications
        """
        self.logger.info("Started listening \U0001f442")
        with self.client.listen_bucket_notification(
            self.bucket_name,
            # prefix="my-prefix/",
            events=["s3:ObjectCreated:*"],
        ) as events:
            for event in events:
                records = event["Records"]
                self.process(records)
                self.logger.info("Continue listening \U0001f442")

    def process(self, messages):
        for message in messages:
            if message["eventName"] == "s3:ObjectCreated:Put":
                filename = message["s3"]["object"]["key"]
                try:

                    document_location = self.get_documents(filename)
                except:
                    self.logger.info("Could not download the file ")
                    traceback.print_exc()
                try:
                    self.updator(document_location)
                except:
                    self.logger.info("Could not update the file in ElasticSearch")
                    traceback.print_exc()
                try:
                    self.deletor(document_location)
                except:
                    self.logger.info("Could not delete the file from the local")
                    traceback.print_exc()
        return "processed"

    def get_documents(self, document_name):
        """
        Add code to get the updated documents from the bucket and save them in local
        """
        self.logger.info(f"Downloading document {document_name} \u2B07\uFE0F")
        if os.path.exists(document_name):
            return document_name

        self.client.fget_object(self.bucket_name, document_name, document_name)
        return document_name

    def updator(self, document_name):
        """
        Add code to read the new documents from local system and push them to the Document Store
        """
        logging.info("Uploading document to document store \u2B06\uFE0F")
        data = json.load(open(document_name, "r"))
        # contents = [
        #     Document(
        #         content=d["content"]
        #     )
        #     for d in data
        # ]
        contents = [
            Document(
                content="A patient asked: "
                + d["input"]
                + ". The doctor answered: "
                + d["output"]
            )
            for d in data
        ]
        self.document_store.write_documents(contents)
        return "updated"
        
    def deletor(self, document_name):
        """
        Delete the files from local once uploaded
        """
        self.logger.info("Deleting file from local \u274C")
        os.remove(document_name)
        return "deleted"

if __name__ == "__main__":
    object = minio_updator()
    object.listener()