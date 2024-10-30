import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse

from parser.pdf_parse import to_chunks, Page
from ollama_proxy import OllamaProxy
from storage import DataStore 


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # app.state.ollama_embed = await OllamaEmbed.create("ollama", 11434)
    app.state.ollama_proxy = await OllamaProxy.create("ollama", 11434)
    app.state.datastore = DataStore(768)
    yield

    # Stop the app


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

@app.post("/add_document")
async def add_document(document: UploadFile):
    document_bytes = await document.read()
    print(f"Received document: {document.filename} of size {len(document_bytes)}")
    ollama_proxy: OllamaProxy = app.state.ollama_proxy
    datastore: DataStore = app.state.datastore
    text_chunks = to_chunks(document_bytes, 512, 128)
    print(f"Document has been parsed in {len(text_chunks)} chunks")
    embeddings = await ollama_proxy.embed(text_chunks)
    print(f"Document has been embedded in {len(embeddings)} chunks")
    document_summary = await ollama_proxy.summarize(text_chunks)
    print(f"Document has been summarized: {document_summary}")
    summary_embedding = await ollama_proxy.embed(document_summary)
    print(f"Summary has been embedded")

    datastore.add_document(
        file_name=document.filename,
        file_bytes=document_bytes,
        summary_embedding=summary_embedding,
        summary_text=document_summary,
        embeddings=embeddings,
        text_chunks=text_chunks
    )

    print(f"Document has been added to the datastore")
    
    return {"status": "ok"}

@app.get("/available_documents")
async def available_documents():

    return app.state.faiss_db.get_all("root")
