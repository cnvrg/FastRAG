# Updater Listener

This library launches a web app that continuously listens to *object creation* events on a specific bucket present on MinIO / S3. When a user uploads any document to the specific MinIO / S3 bucket, the web app   automatically uploads it to the ElasticSearch service. Thus, the next time a user asks a question, if the new document is relevant, that document content is available to the LLM for response generation.

Currently, we support MinIO / S3 object storage for this web app.
The user must provide a few command line arguments to the library to specify the configurations for the MinIO / S3 bucket and the ElasticSearch service.

## Document structure:
The documents uploaded to the minIO / S3 bucket must be formatted as JSON files. A single JSON file may contain multiple documents. The data structure should reflect the example shown:
    [
        {"content": "This is data from document 1"},
        {"content": "This is data from document 2"}
    ]
## Input Args

`--storage_solution` : Type of storage to be used -> MinIo / S3 .(80 - if connecting to an http scheme, 443 if connecting to an https scheme)
`--host_address` : The IP  address of the ElasticSearch service.
`--port` : The port number of the ElasticSearch service.
`--index` : The name of the ElasticSearch index where all the relevant documents are/will be stored for use by RAG.
`--username` : The Username for the ElasticSearch service in case it is protected.
`--password` : The password for the ElasticSearch service in case it is protected.
`--bucket_name` : The Name of the MinIO / S3 bucket that will be connected to the web app for listening.
`--api_link` : The API link to connect with MiniIO.
`--queue_url` : URL to the AWS SNS queue.
`--region_name` : Region name of the AWS bucket.
`--scheme` : https/https scheme

# Web App Configuration
- The web app runs on the same compute template that is used to run this library. 
- The web app runs on a fixed image `harindercnvrg/fastrag:latestv3` irrespective of what you select to run this library.
- Once this library finishes execution, you can find the web app online in the *Webapps* section of the project. 
-  Once the web app is deployed, it displays the status: **Listener Updator is online**.
**Note**: You can connect with Cnvrg team to deploy an ElasticSearch service for you in the backend. When deployed on Cnvrg, the ElasticSearch can only be accessed by resources within the same cluster.

## Input Command

```
python3 updator.py --bucket_name {minio_bucket_name} --index {elasticsearch_index} --port {elasticsearch_port_number} --host {elasticsearch_host_address}--search_field content --api_link minio-standalone.hirshberg.apps.cnvrg.io --access_key {your_minio_accesskey} --secret_key {your_minio_secretkey} 

```
## Sample Input Command

```
python3 updator.py --bucket_name mybucket --index myindex --port 9200 --host 10.42.245.74 --api_link minio-standalone.xxx.apps.cnvrg.io --access_key xxx --secret_key xxx
```

### Instructions on setting up Elastic Search

ElasticSearch (ES) connection is defined using Haystack Library in the `updator_minio.py` file. Currently we support accepting the arguments, `host, port, username, password` to establish the connection with the ES service. In case you have a service provider that has issued additional authetication parameters like api key etc, you can make edits to the `updator_minio.py` file, function `__init__` 
Sometimes, Haystack library may not able to connect with the ES service of your choice out of the box, in that case, it is recommended to make changes in the Haystack library code.

Follow the steps:

1. clone `the haystack repo https://github.com/deepset-ai/haystack`
2. Open the cloned folder.
2. Navigate to the folder, `haystack/document_stores/elasticsearch`
3. Make changes in the elastic search connection in files, `e7.py` or `e8.py` depending on your need.
4. Run command, pip install -e '.[dev]' && pip install -e '.[elasticsearch]'

This should install the haystack library with your changes.

You can read about using ElasticSearch python client directly [here](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)
