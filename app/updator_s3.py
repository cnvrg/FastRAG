import os
import logging
import argparse
import traceback
import dash
from dash_extensions.enrich import Output, Input, html, dcc
from haystack.document_stores import ElasticsearchDocumentStore
from haystack import Document
import boto3
import json
import time

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)

parser = argparse.ArgumentParser(description="Creator")

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

class s3_updator:
    def __init__(self, args):
        self.aws_key_id = args['aws_key_id']
        self.aws_secret_key = args['aws_secret_key']
        self.region_name = args['region_name']

        self.QueueUrl = args['queue_url']
        self.bucket_name = args['bucket_name']

        # define document store resource
        self.document_store = ElasticsearchDocumentStore(
            host=args["host_address"],
            port=args["port"],
            index=args["index"],
            search_fields=["content"],
            refresh_type="false",
            scheme = args["scheme"],
        )

        logging.info("Connected to document store")

        # define SQS resource
        self.sqs = boto3.client(
            "sqs",
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region_name,
        )
        logging.info("SQS client created")

        # define S3 resource
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region_name,
        )
        logging.info("S3 client created")
        self.listener()

    def listener(self):
        """
        Add code for continuous listening to event notifications
        """
        logging.info("Started listening")
        while True:
            response = self.sqs.receive_message(
                QueueUrl=self.QueueUrl,
                AttributeNames=["SentTimestamp"],
                MaxNumberOfMessages=10,
                MessageAttributeNames=["All"],
                VisibilityTimeout=1,
                WaitTimeSeconds=0,
            )

            try:
                response["Messages"]
            except KeyError:
                logging.info("No message in the Queue")
                time.sleep(5)
                continue

            for message in response["Messages"]:
                message = json.loads(response["Messages"][0]["Body"])
                if message["Records"][0]["eventName"] == "ObjectCreated:Put":
                    filename = message["Records"][0]["s3"]["object"]["key"]
                    logging.info(filename)
                    logging.info("Message Received")
                    try:
                        document_location = self.get_documents(filename)
                    except Exception as e:
                        logging.info("Could not download the file ")
                        print(e)
                        continue

                    try:
                        self.updator(document_location)
                    except:
                        logging.info("Could not update the file in Elasticsearch")
                        continue

                    try:
                        self.deletor(document_location)
                    except:
                        logging.info("Could not delete the file from the local")
                        continue

                message = response["Messages"][0]
                receipt_handle = message["ReceiptHandle"]
                logging.info("Deleting message from SQS")
                # Delete received message from queue
                try:
                    self.sqs.delete_message(
                        QueueUrl=self.QueueUrl,
                        ReceiptHandle=receipt_handle,
                    )
                except:
                    logging.info(
                        "Could not delete the message from Queue", receipt_handle
                    )
                    continue

            # code to wait 10 sec

            time.sleep(5)

    def get_documents(self, document_name):
        """
        Add code to get the updated documents from the bucket and save them in local
        """
        logging.info(f"Attempting to download document: {document_name}")
    
        if os.path.exists(document_name):
            logging.info(f"Document already exists locally: {document_name}")
            return document_name
            
        self.s3.download_file(self.bucket_name, document_name, document_name)
        logging.info(f"Document downloaded successfully: {document_name}")
        print(document_name)
        return document_name

    def updator(self, document_name):
        """
        Add code to read the new documents from the local system and push them to the Document Store
        """
        logging.info("Uploading document to document store")
        data = json.load(open(document_name, "r"))
        contents = [
            Document(
                content="A patient asked: "
                + d["input"]
                + ". The doctor answered: "
                + d["output"]
            )
            for d in data
        ]
        print(contents)
        self.document_store.write_documents(contents)
        return "Updated"

    def deletor(self, document_name):
        """
        Delete the files from local once uploaded
        """
        logging.info("deleting file from local")
        os.remove(document_name)

@app.callback(
    Output(component_id="spanner", component_property="children"),
    Input(component_id="load_interval", component_property="n_intervals"),
)
def controller(n_intervals: int):

    with open("commandline_args.txt", "r") as f:
        args = json.load(f)

    obj = s3_updator(args)
    obj.listener()

server = app.server

if __name__ == "__main__":
    app.run_server()
