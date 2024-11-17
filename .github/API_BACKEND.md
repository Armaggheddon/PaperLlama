# Backend APIs

## [GET] /health
- response:
    ```json
    {
        "up_time": 0,
        "status": "string"
    }
    ```
    status can either be "healty" or "unhealthy".

## [GET] /services_health
- response:
    ```json
    {
        "backend": {
            "up_time": 0,
            "status": "string"
        },
        "datastore": {
            "up_time": 0,
            "status": "string"
        },
        "document_converter": {
            "up_time": 0,
            "status": "string"
        }
    }
    ```
    status can either be "healty" or "unhealthy".

## [GET] /has_document_uuid
- request: query parameter
    ```
    /has_document_uuid?document_uuid=xxxxxxx
    ```

- response: 
    ```json
    {
        "has_document": true
    }
    ```

## [GET] /embedding_length
- response:
    ```json
    {
        "embedding_length": 0
    }
    ```

## [POST] /add_document
- request: multipart/form-data, see upload_file function in [**client.py**](../webui/src/remotes/client.py)

- response: 
    ```json
    {
        "is_success": true,
        "message": "string"
    }
    ```
    message is empty if no error occurs. 

> [!NOTE]
> This call can be lengthy depending if this call is the first one or if the document is large in size.

## [POST] /query
- request: 
    ```json
    {
        "text": "string",
        "history": [
            {
                "role": "string",
                "content": "string"
            },
            ...
        ]
    }
    ```
    role is one of "user" or "assistant"

- response: it is a streamed response straight from Ollama. The text produced by the LLM can be obtained by the following:
    ```python
    _json = {"text": user_query, "history": {"role": "assistant", "content": "How can I help you?"}}
    stream_response = requests.post("http://localhost:8000/query", json=_json, stream=True)
    for chunk in stream_response.iter_lines():
        json_chunk = json.loads(chunk)
        text_response = json_chunk["message"]["content"]
    ```
    Each json is sent with a new line character, "\n" and contain the following:
    ```json
    {
        "model": "llama3.2",
        "created_at": "2023-08-04T08:52:19.385406455-07:00",
        "message": {
            "role": "assistant",
            "content": "The",
            "images": null
        },
        "done": false
    }
    ```
    as the Ollama implementation ([link](https://github.com/ollama/ollama/blob/main/docs/api.md#response-9)).

## [POST] /query_document
- request:
    ```json
    {
        "document_uuid": "string",
        "query_str": "string",
        "history": [
            {
                "role": "string",
                "content": "string"
            },
            ...
        ]
    }
    ```
    role is one of "user" or "assistant"
- response: same as [**/query**](#post-query)

## [DELETE] /delete_all
- response:
    ```json
    {
        "is_success": true,
        "error_message": ""
    }
    ```
    if some error happend, "error_message" will contain the reason.

## [DELETE] /delete_document
- request: query parameter
    ```
    http://localhost:8000/delete_document?=document_uuid=xxx
    ```

- response: 
    ```json
    {
        "is_success": true,
        "error_message": ""
    }
    ```
    if some error happend, "error_message" will contain the reason.

## [GET] /document_info
- request: optional query parameter, if not provided the information of all documents stored will be returned. 
    ```
    http://localhost:8000/document_info?=document_uuid=xxx
    ```

- response:
    ```json
    {
        "document_count": 0,
        "documents_info": [
            {
                "document_uuid": "string",
                "document_hash_str": "string",
                "document_filename": "string",
                "document_summary": "string"
            },
            ...
        ]
    }
    ```