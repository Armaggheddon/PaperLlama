# Datastore APIs
Welcome to the Datastore API documentation! These endpoints help you interact with your datastore, from managing documents to running advanced queries. This service uses Faiss for the text embeddings and sqlite3 for the metadata associated to the embedding. It is organized as a hierarchical index with a root index and many sub indexes for each document. Let's explore the APIs! 🌟


## [GET] /health
Check the health of the datastore service.
- **Response**:
    ```json
    {
        "up_time": 0,
        "status": "string"
    }
    ```
    - `up_time`: Runtime of the datastore (in seconds).
    - `status`: `"healthy"` means all systems go; `"unhealthy"` means something’s amiss.


## [GET] /has_document_uuid
Find out if a document exists in the datastore using its UUID.
- **Request**: query parameter
    ```
    /has_document_uuid?document_uuid=xxx
    ```

- **Response**:
    ```json
    {
        "has_document": true
    }
    ```
    - `has_document`: `true` if the document exists, `false` otherwise.


## [GET] /has_document
Check if a document exists using its hash.
- **Request**: query parameter
    ```
    /has_document?document_hash=xxx
    ```

- **Response**:
    ```json
    {
        "has_document": true
    }
    ```
    - `has_document`: `true` if the document exists, `false` otherwise.


## [POST] /add_document
Upload a document to the datastore along with its metadata and embeddings.
- **Request**: 
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
    - `document_filename`: the name of the file written in the shared volume named **uploaded_files_data**.
    - `document_embedding`: the embedded summary that will be used to retrieve the most relevant documents for a given query when interrogating the whole knowledge base.
    - `document_summary`: the summary of the document
    - `document_chunks`: for each text chunk of the document contains its text representation, the page it belongs and the text embedding. 

- **Response**: simply returns **200 OK** or raises **HTTPException** on failure.


## [DELETE] /delete_document
Remove a specific document from the datastore by its UUID.
- **Request**: query parameter
    ```
    /delete_document?document_uuid=xxx
    ```

- **Response**:
    ```json
    {
        "is_success": true,
        "document_filename": "",
        "error_message": ""
    }
    ```
    - `is_success`: `true` if the document was successfully deleted.
    - `document_filename`: Name of the deleted file.
    - `error_message`: Details the reason for failure, if any.

## [DELETE] /delete_all
Wipe all documents and data from the datastore.
- **Response**:
    ```json
    {
        "is_success": true,
        "document_filename": "",
        "error_message": ""
    }
    ```
    - `is_success`: `true` if the document was successfully deleted.
    - `document_filename`: Name of the deleted file.
    - `error_message`: Details the reason for failure, if any.


## [POST] /query_root
Identify documents most likely to be relevant to your query.
- **Request**: 
    ```json
    {
        "query_embedding": [
            0,
            ...
        ]
    }
    ```

- **Response**:
    ```json
    [
        {
            "uuid": "string",
            "summary": "string"
        },
        ...
    ]
    ```
    For each retrieved document there will be:
    - `uuid`: unique identifier for the document, which also represents the document filename without its extension.
    - `summary`: the document's summary.


## [POST] /query_document
Retrieve the most relevant text chunks from specific documents.
- **Request**:
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

- **Response**:
    ```json
    [
        {
            "text": "string",
            "page_number": 0
        },
        ...
    ]
    ```
    For each retrieved chunk there will be:
    - `text`: relevant text extracted from the document.
    - `page_number`: the page in the original PDF file where the text appears.


## [GET] /document_info
Retrieve details about all documents or target one using its UUID.
- **Request**: optional query parameter
    ```
    /document_info?document_uuid=xxx
    ```

- **Response**:
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
    - `document_count`: Total number of stored documents.
    - `documents_info`: A list of documents with details like UUID, filename, and summaries.