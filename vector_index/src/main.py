from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile

from embedding import OllamaEmbed
from .storage import StorageManager 


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    app.state.ollama_embed = await OllamaEmbed.create("ollama", 11434)

    app.state.storage_manager = await StorageManager.create()
    yield

    # Stop the app


app = FastAPI(
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/add_document")
async def add_document(document: UploadFile):
    document_bytes = await document.read()
    embeddings = await app.state.ollama_embed.embed(document_bytes)
    app.state.faiss_db.add("root", embeddings)
    return {"status": "ok"}
