# Document converter APIs

## [GET] /health
- response:
    ```json
    {
        "up_time": 0,
        "status": "string"
    }
    ```
    "status" is either "healty" or "unhealthy"

## [POST] /convert_document
- request:
    ```json
    {
        "document_name": "string",
        "chunk_size": 800
    }
    ```
    "document_name" is the name of the file written in the shared volume named **uploaded_files_data** and chunk size is the maximum size of the chunks that will be returned.

- response:
    ```json
    {
        "text_chunks": [
            "this is the first chunk...",
            ...
        ]
    }
    ```