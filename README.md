# RAG LLM Blueprint

This blueprint is a one click to deploy a RAG pipeline for inference using LLM and updater webapp connected to MinIO / S3 storage solution. User needs to have three external services online before using this blueprint i.e a Large language model, an Elastic Search service and MinIO / S3 storage. User will use the RAG endpoint for inference, which in turn will connect with Elastic Search Service to retrieve latest documents and LLM to generate relevant answers.
The Elastic Search document index will be updated using the webapp that will be deployed along with the RAG endpoint. User needs to update their latest documents in the storage bucket and it will be directly updated in the elastic search document index.

For more information about this blueprint you can refer to [this blog.](https://cnvrg.io/enhance-large-language-models-leveraging-rag-and-minio-and-cnvrg/)

## Technical pre-requisite

1. Setup [ElasticSearch](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)
2. Retrieve the access key either from the llm model hosted on the cnvrg platform or obtain it from OpenAI / Hugging Face.
3. Setup a MinIO / S3 bucket.
4. If the user sets-up an S3 bucket, they also need to configure the SNS queue to capture the object created event. 
- Walkthrough: Configuring a bucket for notifications
    - Step 1: Create an Amazon SQS queue
    - Step 2: Create an Amazon SNS topic
    - Step 3: Add a notification configuration to your bucket
    - Step 4: Test the setup
    
- Refer to the [link](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ways-to-add-notification-config-to-bucket.html) for more information.

## Flow

1. Click on `Use Blueprint` button.
2. You will be redirected to your blueprint flow page.
3. Go to the project settings section and update the [environment variables](https://app.cnvrg.io/docs/core_concepts/projects.html#environment) with relevant information that will be used by the RAG endpoint.

- For more info see the component documentations
    - [RAG endpoint documentation](https://app.af2jdjq262tdqvyelihtqnd.cloud.cnvrg.io/blueprintsdev/blueprints/libraries/rag-endpoint/1.0.51)
    - [Listener/Updator documentation](https://app.af2jdjq262tdqvyelihtqnd.cloud.cnvrg.io/blueprintsdev/blueprints/libraries/listener/1.0.51)
4. You will have to update the task 'updator' to provide relevant information regarding your storage solution and elastic search service.
5. Click on the ‘Run Flow’ button.
6. In a few minutes you will have a RAG endpoint and a webapp deployed to update your elastic search service.
7. Go to the ‘Serving’ tab in the project and look for your endpoint.
8. You can use the Try it Live section to query the RAG endpoint and generate relevant answers with LLM connected.
9. You can also integrate your API with your code using the integration panel at the bottom of the page.

**Note:** A slim version of RAG is also available as a blueprint that enables the use of RAG locally on cnvrg, without the use of Minio / S3 and elasticsearch. Check it out FastRAG slim blueprint for more information.
