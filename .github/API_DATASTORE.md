# Datastore APIs

## [GET] /health
- response:
    ```json
    {
        "up_time": 0,
        "status": "string"
    }
    ```
    "status" is either "healthy" or "unhealthy"

## [GET] /has_document_uuid
- request: query parameter
    ```
    /has_document_uuid?document_uuid=xxx
    ```

- response:
    ```json
    {
        "has_document": true
    }
    ```

## [GET] /has_document
- request: query parameter
    ```
    /has_document?document_hash=xxx
    ```

- response:
    ```json
    {
        "has_document": true
    }
    ```

## [POST] /add_document
- request: 
    ```json
    {
        "document_uuid": "string",
        "document_hash_str": "string",
        "document_filename": "string",
        "document_embedding": [
            0,
            ...
        ],
        "document_summary": "string",
        "document_chunks": [
            {
                "text": "string",
                "page_number": 0,
                "embedding": [
                    0,
                    ...
                ]
            },
            ...
        ]
    }
    ```
    "document_name" is the name of the file written in the shared volume named **uploaded_files_data**.

- response: simply returns 200 OK or raises HTTPException if something fails

## [DELETE] /delete_document
- request: query parameter
    ```
    /delete_document?document_uuid=xxx
    ```

- response:
    ```json
    {
        "is_success": true,
        "document_filename": "",
        "error_message": ""
    }
    ```
    if "is_success" is true, then "document_filename" contains the document name and "error_message" is empty. If is false, then "error_message" will contain the reason while "document_filename" will be empty.

## [DELETE] /delete_all
- response:
    ```json
    {
        "is_success": true,
        "document_filename": "",
        "error_message": ""
    }
    ```
    if "is_success" is true, then "document_filename" contains the document name and "error_message" is empty. If is false, then "error_message" will contain the reason while "document_filename" will be empty.


## [POST] /query_root
- request: 
    ```json
    {
        "query_embedding": [
            0,
            ...
        ]
    }
    ```

- response:
    ```json
    [
        {
            "uuid": "string",
            "summary": "string"
        },
        ...
    ]
    ```
    is a list representing the documents from which content will most likely be relevant to the "query_embedding"

## [POST] /query_document
- request:
    ```json
    {
        "document_uuids": [
            "string",
            ...
        ],
        "query_embedding": [
            ...
        ]
    }
    ```

- response:
    ```json
    [
        {
            "text": "string",
            "page_number": 0
        },
        ...
    ]
    ```
    is a list representing the text chunks that are most relevant to the query extracted from the "document_uuids"


## [GET] /document_info
- request: optional query parameter
    ```
    /document_info?document_uuid=xxx
    ```

- response:
    ```json
    {
        "document_count": 0,
        "document_info": [
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
