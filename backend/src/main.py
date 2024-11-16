from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import uuid
import os
from typing import Optional
import time

from fastapi import FastAPI, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
import httpx
import aiofiles

from ollama_proxy import OllamaProxy

import api_models
import remotes.datastore as datastore
import remotes.document_converter as document_converter


_UPLOADED_FILES_PATH = Path("/uploaded_files")


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    app.state.ollama_proxy = await OllamaProxy.create("ollama", 11434)
    app.state.httpx_client = httpx.AsyncClient()
    
    app.state.startup_time = time.time()
    yield

    # Stop the app
    # app.state.datastore.close()


app = FastAPI(
    lifespan=lifespan
)


@app.get("/health", response_model=api_models.ServiceHealth)
async def health():
    return api_models.ServiceHealth(
        up_time=time.time() - app.state.startup_time,
        status="healthy"
    )

@app.get("/services_health", response_model=api_models.HealthCheckResponse)
async def services_health():
    client: httpx.AsyncClient = app.state.httpx_client
    datastore_uptime = 0
    datastore_status_str = "unhealthy"
    try:
        datastore_health_response = await client.get(
            datastore.HEALTH_URL)
        if datastore_health_response.status_code == status.HTTP_200_OK:
            datastore_health = datastore.HealthCheckResponse(
                **datastore_health_response.json()
            )
            datastore_uptime = datastore_health.up_time
            datastore_status_str = datastore_health.status
    except httpx.ConnectTimeout:
        pass
    
    document_converter_uptime = 0
    document_converter_status_str = "unhealthy"
    try:
        document_converter_health = await client.get(
            document_converter.HEALTH_URL)
        if document_converter_health.status_code == status.HTTP_200_OK:
            document_converter_health = document_converter.HealthCheckResponse(
                **document_converter_health.json()
            )
            document_converter_uptime = document_converter_health.up_time
            document_converter_status_str = document_converter_health.status
    except httpx.ConnectTimeout:
        pass
    
    return api_models.HealthCheckResponse(
        backend=api_models.ServiceHealth(
            up_time=time.time() - app.state.startup_time,
            status="healthy"
        ),
        datastore=api_models.ServiceHealth(
            up_time=datastore_uptime,
            status=datastore_status_str
        ),
        document_converter=api_models.ServiceHealth(
            up_time=document_converter_uptime,
            status=document_converter_status_str
        )
    )


@app.get("/has_document_uuid", response_model=datastore.HasDocumentResponse)
async def has_document_uuid(document_uuid: str):
    print(f"Checking if document with uuid {document_uuid} exists")
    client: httpx.AsyncClient = app.state.httpx_client

    has_document_response = await client.get(
        datastore.HAS_DOCUMENT_UUID_URL,
        params={"document_uuid": document_uuid}
    )
    has_document_json = has_document_response.json()
    return datastore.HasDocumentResponse(**has_document_json)


@app.get("/embedding_length")
async def get_embedding_length():
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    return {"embedding_length": ollama_proxy.embed_model_output}


@app.post("/add_document", response_model=api_models.UploadFileResponse)
async def add_document(document: UploadFile):
    document_bytes = await document.read()
    if not document.filename.endswith(".pdf"):
        return api_models.UploadFileResponse(is_success=False, message="Only PDF files are supported")
    
    print(f"Received document: {document.filename} of size {len(document_bytes)}")
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    client: httpx.AsyncClient = app.state.httpx_client

    document_hash = hashlib.md5(document_bytes).hexdigest()
    document_ext = document.filename.split(".")[-1]
    document_name = f"{document_hash}.{document_ext}"

    has_document_response = await client.get(
        datastore.HAS_DOCUMENT_URL,
        params={"document_hash": document_hash}
    )
    if has_document_response.json()["has_document"]:
        return api_models.UploadFileResponse(is_success=False, message="Document already exists in the datastore")
    
    document_uuid = str(uuid.uuid4())
    async with aiofiles.open(str(_UPLOADED_FILES_PATH / document_name), "wb") as f:
        await f.write(document_bytes)
 
    document_parse_response = await client.post(
        url=document_converter.CONVERT_DOCUMENT_URL,
        json=document_converter.ConvertDocumentRequest(
            document_name=document_name).model_dump(),
        timeout=None
    )
    if document_parse_response.status_code != status.HTTP_200_OK: 
        return api_models.UploadFileResponse(
            is_success=False, 
            message="Document parsing failed"
        )
    
    document_parse_response_json = document_parse_response.json()
    text_chunks = document_converter.ConvertDocumentResponse(
        **document_parse_response_json).text_chunks
    
    embeddings = await ollama_proxy.embed(text_chunks)
    document_summary = await ollama_proxy.summarize(text_chunks)
    summary_embedding = await ollama_proxy.embed(document_summary)

    datastore_request = datastore.AddDocumentRequest(
        document_uuid=document_uuid,
        document_hash_str=document_hash,
        document_filename=document_name,
        document_embedding=summary_embedding[0],
        document_summary=document_summary,
        document_chunks=[
            datastore.AddDocumentChunk(
                text=chunk,
                page_number=i,
                embedding=embedding
            )
            for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings))
        ]
    )

    datastore_response = await client.post(
        datastore.ADD_DOCUMENT_URL,
        json=datastore_request.model_dump(),
        timeout=None
    )
    if datastore_response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Datastore failed to add document")
    
    return api_models.UploadFileResponse(is_success=True)


@app.post("/query")
async def query(request: api_models.QueryRequest):
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    client: httpx.AsyncClient = app.state.httpx_client

    embedded_query = await ollama_proxy.embed(request.text)

    documents_response = await client.post(
        datastore.QUERY_ROOT_URL,
        json=datastore.RootQueryRequest(
            query_embedding=embedded_query[0]
        ).model_dump()
    )
    if documents_response.status_code != status.HTTP_200_OK:
        return {"message": {"content": "No relevant documents found", "type": "error"}}
    
    root_documents = [
        datastore.RootQueryResult(**doc) for doc in documents_response.json()
    ]
    document_query_request = datastore.DocumentQueryRequest(
        document_uuids=[doc.uuid for doc in root_documents],
        query_embedding=embedded_query[0]
    )

    chunks_text_response = await client.post(
        datastore.QUERY_DOCUMENT_URL,
        json=document_query_request.model_dump()
    )
    # print(chunks_text_response.json())
    if chunks_text_response.status_code != status.HTTP_200_OK:
        return {"message": {"content": "No relevant documents found", "type": "error"}}
    
    chunk_texts = [
        datastore.DocumentChunk(**chunk) for chunk in chunks_text_response.json()]
    
    text_chunks = [doc_info.text for doc_info in chunk_texts]
    reranked_chunk_texts = await ollama_proxy.rerank(request.text, text_chunks)
    if not reranked_chunk_texts:
        return {"message": {"content": "No relevant documents found", "type": "error"}}
    
    return StreamingResponse(
        ollama_proxy.chat(
            user_input=request.text, 
            chat_history=request.history,
            context=reranked_chunk_texts
        ),
        media_type="application/x-ndjson"
    )

@app.post("/query_document")
async def query_document(request: api_models.QueryDocumentRequest):
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    client: httpx.AsyncClient = app.state.httpx_client

    query_embedding = await ollama_proxy.embed(request.query_str)
    document_query_request = datastore.DocumentQueryRequest(
        document_uuids=[request.document_uuid],
        query_embedding=query_embedding[0]
    )
    document_query_response = await client.post(
        datastore.QUERY_DOCUMENT_URL,
        json=document_query_request.model_dump()
    )

    if document_query_response.status_code != status.HTTP_200_OK:
        return {"message": {"content": "No relevant documents found", "type": "error"}}
    
    chunk_texts = [
        datastore.DocumentChunk(**chunk) for chunk in document_query_response.json()]
    
    text_chunks = [doc_info.text for doc_info in chunk_texts]
    reranked_chunk_texts = await ollama_proxy.rerank(request.query_str, text_chunks)
    if not reranked_chunk_texts:
        return {"message": {"content": "No relevant documents found", "type": "error"}}
    
    return StreamingResponse(
        ollama_proxy.chat(
            user_input=request.query_str, 
            chat_history=request.history,
            context=reranked_chunk_texts
        ),
        media_type="application/x-ndjson"
    )


@app.delete("/delete_all", response_model=api_models.DeleteDocumentResponse)
async def delete_all():
    
    client: httpx.AsyncClient = app.state.httpx_client

    delete_all_response = await client.delete(
        datastore.DELETE_ALL_DOCUMENTS_URL
    )
    
    for file in os.listdir(str(_UPLOADED_FILES_PATH)):
        os.remove(os.path.join(str(_UPLOADED_FILES_PATH), file))

    if delete_all_response.status_code != status.HTTP_200_OK:
        return api_models.DeleteDocumentResponse(
            is_success=False, 
            error_message="Datastore failed to delete all documents"
        )

    return api_models.DeleteDocumentResponse(is_success=True)

@app.delete("/delete_document", response_model=api_models.DeleteDocumentResponse)
async def delete_document(document_uuid: str):
    
    client: httpx.AsyncClient = app.state.httpx_client

    delete_document_response = await client.delete(
        datastore.DELETE_DOCUMENT_URL,
        params={"document_uuid": document_uuid}
    )

    if delete_document_response.status_code != status.HTTP_200_OK:
        return api_models.DeleteDocumentResponse(
            is_success=False, 
            error_message="Datastore failed to delete document"
        )
    
    delete_document = datastore.DocumentDeleteResponse(
        **delete_document_response.json()
    )

    if not delete_document.is_success:
        return api_models.DeleteDocumentResponse(
            is_success=False, 
            error_message=delete_document.error_message
        )

    document_filename = delete_document.document_filename
    if not document_filename:
        return api_models.DeleteDocumentResponse(
            is_success=False, 
            error_message="Document not found"
        )
    
    _document_path = os.path.join(str(_UPLOADED_FILES_PATH), document_filename)
    if os.path.isfile(_document_path):
        os.remove(_document_path)

    return api_models.DeleteDocumentResponse(is_success=True)


@app.get("/document_info", response_model=datastore.DocumentInfoResponse)
async def available_documents(document_uuid: Optional[str] = None):
    client: httpx.AsyncClient = app.state.httpx_client

    documents_info_response = await client.get(
        datastore.DOCUMENT_INFO_URL,
        params={"document_uuid": document_uuid} if document_uuid else None
    )

    if documents_info_response.status_code != status.HTTP_200_OK:
        return {"status": "error"}
    
    response = datastore.DocumentInfoResponse(**documents_info_response.json())
    return response
