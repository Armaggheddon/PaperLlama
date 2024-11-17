# Document converter APIs
Welcome to the Document Converter API! This service specializes in converting documents into digestible text chunks, making them ready for further processing. This service makes use of the Docling library; check it out [**here**](https://github.com/DS4SD/docling). Let’s dive in the APIs! 🌟

## [GET] /healthCheck the health of the document converter service.
Check the health of the document converter service.
- **Response**:
    ```json
    {
        "up_time": 0,
        "status": "string"
    }
    ```
    - `up_time`: runtime of the service (in seconds).
    - `status`: `"healthy"` means the service is good to go; `"unhealthy"` means something's wrong.


## [POST] /convert_document
Convert a document into smaller, structured text chunks. Process a document from the shared volume and split it into chunks of a specified size.
- **Request**:
    ```json
    {
        "document_name": "string",
        "chunk_size": 800
    }
    ```
    - `document_name`: name of the file written in the shared volume named **uploaded_files_data** and chunk size is the maximum size of the chunks that will be returned.
    - `chunk_size`: maximum size (in characters) of each resulting text chunk.

- **Response**:
    ```json
    {
        "text_chunks": [
            "this is the first chunk...",
            ...
        ]
    }
    ```
    - `text_chunks`: A list of sequential text chunks extracted from the document.