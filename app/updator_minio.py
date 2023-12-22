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
import dash
from dash_extensions.enrich import Output, html
from threading import Thread

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description="""Creator""")

## These areguments are not used. They are added to avoid an error in Cnvrg.
parser.add_argument(
    "--timeout",
    action="store",
    dest="timeout",
    required=False,
    help="""path to the classes.json file""",
)
parser.add_argument(
    "--workers",
    action="store",
    dest="workers",
    required=False,
    help="""directory containing all pdf files""",
)
parser.add_argument(
    "-b",
    action="store",
    dest="b",
    required=False,
    help="""Label names you want to associate the files with""",
)

parser.add_argument(
    "--access-logfile",
    action="store",
    dest="access-logfile",
    required=False,
    help="""Label names you want to associate the files with""",
)

parser.add_argument(
    "--error-logfile",
    action="store",
    dest="error-logfile",
    required=False,
    help="""Label names you want to associate the files with""",
)

class minio_updator:
    def __init__(self, args):
        self.bucket_name = args["bucket_name"]
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
            host=args["host_address"],
            port=args["port"],
            index=args["index"],
            username=os.environ['ELASTIC_USERNAME'],
            password=os.environ['ELASTIC_PASSWORD'],
            search_fields=["content"],
            refresh_type="false",
            scheme = args['scheme']
        )

        self.logger.info("Connected to Elastic Search \u2705")

        # define MinIO client
        self.client = Minio(
            args["api_link"],
            access_key=args['access_key'],
            secret_key=args['secret_key'],
            secure=False,
        )
        self.logger.info("MinIO client connected \u2705")
        

    def listener(self):
        self.logger.info("Started listening \U0001f442")
        with self.client.listen_bucket_notification(
            self.bucket_name,
            events=["s3:ObjectCreated:*"],
        ) as events:
            for event in events:
                records = event["Records"]
                self.logger.info(f"Received Minio event: {records}")
                self.process(records)
                self.logger.info("Continue listening \U0001f442")

    def process(self, messages):
        for message in messages:
            if message["eventName"] == "s3:ObjectCreated:Put":
                filename = message["s3"]["object"]["key"]
                try:
                    document_location = self.get_documents(filename)
                    self.logger.info(f"Downloaded document from Minio: {document_location}")
                except:
                    self.logger.info("Could not download the file ")
                    traceback.print_exc()
                try:
                    self.updator(document_location)
                    self.logger.info("Updated document in Elasticsearch")
                except:
                    self.logger.info("Could not update the file in Elasticsearch")
                    traceback.print_exc()
                try:
                    self.deletor(document_location)
                    self.logger.info("Deleted file from local")
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

class MinioUpdatorApp:
    def __init__(self, minio_updator_instance):
        self.minio_updator = minio_updator_instance
        self.app = dash.Dash(__name__)
        self.app.layout = self.create_layout()
        self.callback_functions()

        self.start_listener()

    def create_layout(self):
        return html.Div(
            [
                html.H1("Updator Dash App"),
                html.Div(id="output-message"),
            ]
        )

    def callback_functions(self):
        pass

    def start_listener(self):
        # Start the listener in a separate thread
        self.listener_thread = Thread(target=self.minio_updator.listener)
        self.listener_thread.start()

    def run(self):
        self.app.run_server(debug=True)

def create_app():
    with open("commandline_args.txt", "r") as f:
        args = json.load(f)

    minio_updator_instance = minio_updator(args)  # Pass the arguments to the constructor
    minio_app = MinioUpdatorApp(minio_updator_instance)
    return minio_app.app.server  # Return the Flask server instead of the Dash app

server = create_app()

if __name__ == "__main__":
    server.run(port=8500, debug=True)

