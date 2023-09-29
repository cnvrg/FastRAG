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

app = dash.Dash("")

app.layout = html.Div(
    children=[
        html.H1(children="Listener Updator is online"),
        # within layout
        dcc.Interval(
            id="load_interval",
            n_intervals=0,
            max_intervals=0,  # <-- only run once
            interval=1,
        ),
        html.Span(
            id="spanner", style=dict(color="yellow")  # <-- just so it's easy to see
        ),
    ]
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
            username= args['username'],
            password=args['password'],
            search_fields=["content"],
            refresh_type="false",
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

@app.callback(
    Output(component_id="spanner", component_property="children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def controller(n_intervals: int):

    with open("commandline_args.txt", "r") as f:
        args = json.load(f)

    object = minio_updator(args)
    object.listener()


server = app.server

if __name__ == "__main__":
    app.run_server() 