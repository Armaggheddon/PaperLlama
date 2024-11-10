import asyncio
from contextlib import asynccontextmanager
from genericpath import isfile
from http import client
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor
import uuid
import os

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
    
    # app.state.ollama_embed = await OllamaEmbed.create("ollama", 11434)
    app.state.ollama_proxy = await OllamaProxy.create("ollama", 11434)
    app.state.httpx_client = httpx.AsyncClient()
    # app.state.datastore = DataStore(app.state.ollama_proxy.embed_model_output)
    yield

    # Stop the app
    # app.state.datastore.close()


app = FastAPI(
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


async def generate_response():
    very_long_text = "In a far away galaxy, there was a planet called Ollama. On this planet, there were many creatures, but the most interesting of them all were the Ollamas. The Ollamas were a very intelligent species, and they had the ability to communicate with each other using a special language called Ollamish. The Ollamas were also very friendly and peaceful, and they lived in harmony with the other creatures on the planet. One day, a group of scientists from Earth arrived on Ollama to study the planet and its inhabitants. The scientists were amazed by the Ollamas and their unique language, and they spent many years learning about them. Eventually, the scientists were able to communicate with the Ollamas and learn from them. The Ollamas shared their knowledge of the planet and its history with the scientists, and together they made many important discoveries. The scientists were so impressed by the Ollamas that they decided to stay on the planet and continue their research. And so, the Ollamas and the scientists lived together in peace and harmony, sharing their knowledge and wisdom with each other for many years to come."
    for i in range(len(very_long_text)):
        await asyncio.sleep(0.01)
        yield f"{very_long_text[i]}"


@app.get("/embedding_length")
async def get_embedding_length():
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    return {"embedding_length": ollama_proxy.embed_model_output}


@app.get("/chat-stream")
async def stream_response(text):
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    return StreamingResponse(ollama_proxy.chat(text), media_type="text/event-stream")

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
        # print(document_parse_response.text) 
        return api_models.UploadFileResponse(is_success=False, message="Document parsing failed")
    
    document_parse_response_json = document_parse_response.json()
    text_chunks = document_converter.ConvertDocumentResponse(**document_parse_response_json).text_chunks
    
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

    # if datastore.get_document_count() == 0:
    #     return {"message": {"content": "No documents in the datastore", "type": "error"}}

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
        ollama_proxy.chat(request.text, reranked_chunk_texts), 
        # media_type="application/json"
        media_type="application/x-ndjson"
    )

@app.delete("/delete_all")
async def delete_all(delete_all_request: api_models.DeleteAllRequest):
    if not delete_all_request.confirm:
        return {"status": "confirm must be true to delete all documents"}
    
    client: httpx.AsyncClient = app.state.httpx_client

    delete_all_response = await client.delete(
        datastore.DELETE_ALL_DOCUMENTS_URL
    )
    
    for file in os.listdir(str(_UPLOADED_FILES_PATH)):
        os.remove(os.path.join(str(_UPLOADED_FILES_PATH), file))

    if delete_all_response.status_code != status.HTTP_200_OK:
        return {"status": "error"}

    return {"status": "ok"}

@app.delete("/delete_document")
async def delete_document(document_uuid: str):
    
    client: httpx.AsyncClient = app.state.httpx_client

    delete_document_response = await client.delete(
        datastore.DELETE_DOCUMENT_URL,
        params={"document_uuid": document_uuid}
    )

    if delete_document_response.status_code != status.HTTP_200_OK:
        return {"status": "error"}
    
    document_filename = delete_document_response.json()["document_filename"]
    if not document_filename:
        return {"status": "File does not exist in the datastore"}
    
    _document_path = os.path.join(str(_UPLOADED_FILES_PATH), document_filename)
    if os.path.isfile(_document_path):
        os.remove(_document_path)

    return {"status": "ok"}

@app.get("/documents_info")
async def available_documents():
    client: httpx.AsyncClient = app.state.httpx_client

    documents_info_response = await client.get(
        datastore.DOCUMENTS_INFO_URL
    )

    if documents_info_response.status_code != status.HTTP_200_OK:
        return {"status": "error"}
    
    return documents_info_response.json()
