# RAG Endpoint

This library deploys an endpoint on Cnvrg that is used to ask questions and generate relevant answers, based on the documents present in the connected ElasticSearch index. This endpoint connects with a Large Language Model and ElasticSearch service, based on the information provided in the environment variables. Currently we support:

- txt-to-txt generation models from huggingface
- LLMs hosted on Cnvrg (Models hosted on cnvrg must accept input in form of dictionary with key prompt {"prompt": "your prompt goes here} )
- OpenAI InstructGPT models.

## Flow

1. The User asks RAG endpoint a question
2. The RAG Endpoint retrieves top n relevant documents from ElasticSearch document index. (BM25Retriever is used)
3. The RAG Endpoint re-ranks the documents to have only top k results. (ColbertRanker is used)
4. The RAG Endpoint shares the top k results along with the user-defined prompt to the LLM.
5. The response generated by the LLM is returned to the user.

## Setup 

The user  must add a few environment variables in order to deploy and use the RAG endpoint. [Setting up Environment Variables in Cnvrg.](https://app.cnvrg.io/docs/core_concepts/projects.html#environment)

### Dataset setup
The user must add the documents to the cnvrg dataset in a json format

Sample of the dataset document for reference:

```
[
    {
        "instruction": "If you are a doctor, please answer the medical questions based on the patient's description.",
        "input": "Doctor, I have been experiencing shoulder swelling, chills, hand or finger pain, and back pain. What could be the reason for this?",
        "output": "It seems like you might have Valley fever."
    },
    {
        "instruction": "If you are a doctor, please answer the medical questions based on the patient's description.",
        "input": "Doctor, I injured my hand and it's really painful. What tests do you recommend?",
        "output": "Based on your description of your injury, I would recommend a radiographic imaging procedure, also known as a plain x-ray, to determine the extent of the damage. Depending on the results, we may need to apply a splint or suture any wounds. We will also need to manage the wound care and may recommend physical therapy exercises to aid in your recovery. In addition, an occupational therapy assessment may be necessary to determine if speech therapy is needed."
    }

]
``` 
Note: Adjusting the document's format is possible to meet the model's requirements. However, it's essential to modify how the fucntion `updator` within the `predict.py` script accesses the document.
``` 
Note: Adjusting the document's format is possible to meet the model's requirements. However, it's essential to modify how the fucntion `updator` within the `predict.py` script accesses the document.

### ElasticSearch setup variables
`ELASTIC_PORT` = The port number of the ElasticSearch service. (80 - if connecting to an http scheme, 443 if connecting to an https scheme)

`ELASTIC_HOST` = The IP address of the ElasticSearch service.

`ELASTIC_INDEX` = The name of the ElasticSearch index where all the relevant documents are stored for use by RAG.

`ELASTIC_USERNAME` = The username for the ElasticSearch service in case it is protected.

`ELASTIC_PASSWORD` = The password for the ElasticSearch service in case it is protected.

### ElasticSearch secret variables

`MINIO_ACCESS_KEY` : The access key to connect with MinIO.
`MINIO_SECRET_KEY` :  The secret key to connect with MinIO.

`AWS_ACCESS_KEY` : The access key to connect with AWS/S3.
`AWS_SECRET_KEY` :  The secret key to connect with AWS/S3.


### LLM setup variables
`PROVIDER` = The name of the LLM service provider. Acceptable values are: `huggingface` , `openai` and `cnvrg`

`MODEL_NAME` = in case the LLM is provided by huggingface, provide repo id for example: `google/flan-t5-xl` or if the model is provided by openAI provide model name for example: `gpt-3.5-turbo`

`PROMPT` = Enter the prompt you want to share with the LLM. Your prompt will include the question you ask the RAG endpoint and the documents. Query and documents will be automatically inserted in the placeholders. An example prompt is given below.

    
    Below is an instruction that describes a task paired with an input, which provides further context. Write a response that appropriately completes the request.

    ### Instruction:
    You are a doctor. Synthesize a comprehensive answer from the following Input and the question: {query}

    ### Input:
    paragraphs: {documents}

    ### Response:
        

`LLM_API_KEY` = Your API key provided by the service provider. 

`URL` = The URL of your model in case it is deployed as endpoint on cnvrg..

**Note:** For users whose LLM model is hosted on Cnvrg, follow the steps below to get the API_KEY and URL. 

Once deployed, go to the endpoint page and scroll down.

    curl -X POST \
        https://your-endpoint.cloud.cnvrg.io/api/v1/endpoints/XYZ \
    -H 'Cnvrg-Api-Key: XXXX' \
    -H 'Content-Type: application/json' \
    -d '{"input_params": "your_input_params"}'
    
`https://your-endpoint.cloud.cnvrg.io/api/v1/endpoints/XYZ` is your `URL`
`XXXX` is your `API_KEY`

### RAG setup variables

`RETRIEVER_N` = The  number of top documents you want the retriever to retrieve from the ElasticSearch index. For example 20.

`RANKER_N` = The  number of top documents you want to send to the LLM after re-ranking. For example 5.

`SCHEME` = The https/https scheme


### Instructions on setting up Elastic Search

ElasticSearch (ES) connection is defined using Haystack Library in the `predict.py` file. Currently we support accepting the arguments, `host, port, username, password` to establish the connection with the ES service. In case you have a service provider that has issued additional authetication parameters like api key etc, you can make edits to the `predict.py` file, function `RAG_pipeline.`
Sometimes, Haystack library may not able to connect with the ES service of your choice, in that case, it is recommended to make changes in the Haystack library code.

Follow the steps:

1. clone `the haystack repo https://github.com/deepset-ai/haystack`
2. Open the cloned folder.
2. Navigate to the folder, `haystack/document_stores/elasticsearch`
3. Make changes in the elastic search connection in files, `e7.py` or `e8.py` depending on your need.
4. Run command, pip install -e '.[dev]' && pip install -e '.[elasticsearch]'

This should install the haystack library with your changes.

You can read about using ElasticSearch python client directly [here](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)

# References

[deepset-ai](https://github.com/deepset-ai/haystack)
[IntelLabs](https://github.com/IntelLabs/fastRAG/tree/main)