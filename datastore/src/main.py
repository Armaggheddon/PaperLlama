import asyncio
import httpx
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, status

import api_models
from storage import DataStore

@asynccontextmanager
async def lifespan(app: FastAPI):

    embeddings_length = 0
    _transport = httpx.AsyncHTTPTransport(retries=3)
    async with httpx.AsyncClient(transport=_transport) as client:
        response = await client.get("http://backend:8000/embedding_length")
        embeddings_length = response.json()["embedding_length"]

    app.state.datastore = DataStore(embeddings_length)
    
    yield

    app.state.datastore.close()


app = FastAPI(
    lifespan=lifespan,
    title="Datastore API",
)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/has_document_uuid")
async def has_document_uuid(document_uuid: str):
    datastore: DataStore = app.state.datastore
    return {"has_document_uuid": datastore.has_document_uuid(document_uuid)}

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

@app.delete("/delete_document")
async def delete_document(document_uuid: str):
    datastore: DataStore = app.state.datastore
    if not datastore.has_document_uuid(document_uuid):
        return {"document_filename": None}
    document_filename = datastore.delete_document(document_uuid)
    return {"document_filename": document_filename}

@app.delete("/delete_all")
async def delete_all():
    datastore: DataStore = app.state.datastore
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, datastore.clear)

@app.post("/query_root", response_model=list[api_models.RootQueryResult])
async def query_root(request: api_models.RootQueryRequest):
    datastore: DataStore = app.state.datastore
    return datastore.query_root(request.query_embedding)
    

@app.post("/query_document")
async def query_document(request: api_models.DocumentQueryRequest):
    datastore: DataStore = app.state.datastore
    return datastore.query_documents(request.document_uuids, request.query_embedding)

@app.get("/documents_info", response_model=api_models.DocumentInfoResponse)
async def documents_info():
    datastore: DataStore = app.state.datastore
    return datastore.get_documents_info()