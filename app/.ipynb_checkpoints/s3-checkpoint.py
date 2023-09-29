from haystack.document_stores import ElasticsearchDocumentStore
from haystack import Document
import boto3
import json
import time
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)


class s3_updator:
    def __init__(self):
        self.aws_key_id = 'AKIAVGKKBLADZYUFFIEQ'
        self.aws_secret_key = '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'
        self.region_name = 'us-east-2'

        self.QueueUrl = 'https://sqs.us-east-2.amazonaws.com/357174433799/myq'
        self.bucket_name = 'ragq'

        # define document store resource
        self.document_store = ElasticsearchDocumentStore(
            host='10.42.6.227',
            port='9200',
            index='test',
            search_fields=["content"],
            refresh_type="false",
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

        # define s3 resource
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
        Add code for conitnous listening to event notifications
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
                        logging.info("Could not update the file in ElasticSearch")
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

            time.sleep(10)

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
        return document_name
    

    def updator(self, document_name):
        """
        Add code to read the new documents from local system and push them to the Document Store
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
        self.document_store.write_documents(contents)
        return "Updated"

    def deletor(self, document_name):
        """
        Delete the files from local once uploaded
        """
        logging.info("deleting file from local")
        os.remove(document_name)

if __name__ == "__main__":
    #load the arguments
    object = s3_updator()
    object.listener()