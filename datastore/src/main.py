import asyncio
import httpx
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import time
import sys

from fastapi import FastAPI, HTTPException, status

import api_models
from storage import DataStore

@asynccontextmanager
async def lifespan(app: FastAPI):

    embeddings_length = 0
    curr_retry = 0
    max_retries = 5
    while curr_retry < max_retries:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://backend:8000/embedding_length")
                embeddings_length = response.json()["embedding_length"]
                break # break loop, response was successful
        except Exception as e:
            curr_retry += 1
            print(
                f"[{curr_retry}] Error getting embedding length from backend"
                f", retrying in 5s: {e}", file=sys.stderr)
            await asyncio.sleep(5)
    
    if embeddings_length == 0:
        raise RuntimeError("Could not get embedding length from backend")

    app.state.datastore = DataStore(embeddings_length)

    app.state.startup_time = time.time()
    
    yield

    app.state.datastore.close()


app = FastAPI(
    lifespan=lifespan,
    title="Datastore API",
)


@app.get("/health", response_model=api_models.HealthCheckResponse)
async def health():
    return api_models.HealthCheckResponse(
        up_time=time.time() - app.state.startup_time,
        status="healthy"
    )

@app.get("/has_document_uuid")
async def has_document_uuid(document_uuid: str):
    datastore: DataStore = app.state.datastore
    return api_models.HasDocumentResponse(has_document=datastore.has_document_uuid(document_uuid))

@app.get("/has_document", response_model=api_models.HasDocumentResponse)
async def has_document(document_hash: str):
    datastore: DataStore = app.state.datastore
    return api_models.HasDocumentResponse(has_document=datastore.has_document(document_hash))

@app.get("/has_document_uuid", response_model=api_models.HasDocumentResponse)
async def has_document_uuid(document_uuid: str):
    datastore: DataStore = app.state.datastore
    return api_models.HasDocumentResponse(has_document=datastore.has_document_uuid(document_uuid))

@app.post("/add_document")
async def add_document(request: api_models.AddDocumentRequest):
    datastore: DataStore = app.state.datastore
    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        add_document_args = [
            request.document_uuid,
            request.document_hash_str,
            request.document_filename,
            request.document_embedding,
            request.document_summary,
            request.document_chunks
        ]
        try:
            await loop.run_in_executor(
                pool,
                datastore.add_document,
                *add_document_args
            )
        except ValueError as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

@app.delete("/delete_document", response_model=api_models.DocumentDeleteResponse)
async def delete_document(document_uuid: str):
    datastore: DataStore = app.state.datastore
    if not datastore.has_document_uuid(document_uuid):
        return api_models.DocumentDeleteResponse(
            is_success=False, 
            error_message="Document not found"
        )
    document_filename = datastore.delete_document(document_uuid)
    return api_models.DocumentDeleteResponse(
        is_success=True, 
        document_filename=document_filename
    )

@app.delete("/delete_all", response_model=api_models.DocumentDeleteResponse)
async def delete_all():
    datastore: DataStore = app.state.datastore
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, datastore.clear)
    return api_models.DocumentDeleteResponse(is_success=True)

@app.post("/query_root", response_model=list[api_models.RootQueryResult])
async def query_root(request: api_models.RootQueryRequest):
    datastore: DataStore = app.state.datastore
    return datastore.query_root(request.query_embedding)
    

@app.post("/query_document", response_model=list[api_models.DocumentChunk])
async def query_document(request: api_models.DocumentQueryRequest):
    datastore: DataStore = app.state.datastore
    return datastore.query_documents(request.document_uuids, request.query_embedding)

@app.get("/document_info", response_model=api_models.DocumentInfoResponse)
async def documents_info(document_uuid: Optional[str] = None):
    datastore: DataStore = app.state.datastore
    return datastore.get_document_info(document_uuid)