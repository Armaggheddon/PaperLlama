import asyncio
from contextlib import asynccontextmanager
from operator import is_
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
import ollama
from concurrent.futures import ThreadPoolExecutor

from parser.pdf_parse import to_chunks
from ollama_proxy import OllamaProxy
from storage import DataStore 

import api_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # app.state.ollama_embed = await OllamaEmbed.create("ollama", 11434)
    app.state.ollama_proxy = await OllamaProxy.create("ollama", 11434)
    app.state.datastore = DataStore(app.state.ollama_proxy.embed_model_output)
    yield

    # Stop the app
    app.state.datastore.close()


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
    datastore: DataStore = app.state.datastore

    if datastore.has_document(document_bytes):
        return api_models.UploadFileResponse(is_success=False, message="Document already exists in the datastore")

    text_chunks = to_chunks(document_bytes, 256, 32)
    print(f"Document has been parsed in {len(text_chunks)} chunks")
    embeddings = await ollama_proxy.embed(text_chunks)
    print(f"Document has been embedded in {len(embeddings)} chunks")
    document_summary = await ollama_proxy.summarize(text_chunks)
    print(f"Document has been summarized: {document_summary}")
    summary_embedding = await ollama_proxy.embed(document_summary)
    print(f"Summary has been embedded")

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        add_document_args = {
            "file_name": document.filename,
            "file_bytes": document_bytes,
            "summary_embedding": summary_embedding,
            "summary_text": document_summary,
            "embeddings": embeddings,
            "text_chunks": text_chunks
        }
        await loop.run_in_executor(
            pool,
            datastore.add_document,
            *(list(add_document_args.values()))
        )

    print(f"Document has been added to the datastore")
    
    return api_models.UploadFileResponse(is_success=True)

@app.get("/query")
async def query(text):
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    datastore: DataStore = app.state.datastore

    query_embedding = await ollama_proxy.embed(text)
    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        chunk_texts = await loop.run_in_executor(
            pool,
            datastore.query,
            query_embedding
        )

    return StreamingResponse(
        ollama_proxy.chat(text, chunk_texts), 
        # media_type="application/json"
        media_type="application/x-ndjson"
    )

@app.post("/delete_all")
async def delete_all(delete_all_request: api_models.DeleteAllRequest):
    if not delete_all_request.confirm:
        return {"status": "confirm must be true to delete all documents"}
    datastore: DataStore = app.state.datastore
    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(
            pool,
            datastore.delete_all
        )

    return {"status": "ok"}

@app.post("/delete_document_by_id")
async def delete_document_by_id(delete_document_request: api_models.DeleteIndexIdsRequest):
    datastore: DataStore = app.state.datastore

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(
            pool,
            datastore.delete_document_by_ids,
            delete_document_request.index_ids
        )

    return {"status": "ok"}

@app.get("/available_documents")
async def available_documents():
    datastore: DataStore = app.state.datastore

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        documents = await loop.run_in_executor(
            pool,
            datastore.get_all_documents
        )

    return documents
