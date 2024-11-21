import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import time

from fastapi import FastAPI, HTTPException, status

from converter import DoclingDocumentConverter
import api_models


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.converter = await DoclingDocumentConverter.create()
    app.state.startup_time = time.time()

    yield


app = FastAPI(
    lifespan=lifespan,
    title="Document Converter API",
)

@app.get("/health", response_model=api_models.HealthCheckResponse)
async def health():
    """
    Health check endpoint that returns the status of the service.
    """
    return api_models.HealthCheckResponse(
        up_time=time.time() - app.state.startup_time,
        status="healthy"
    )


@app.post("/convert_document", response_model=api_models.ConvertDocumentResponse)
async def convert_document(request: api_models.ConvertDocumentRequest):
    """
    Converts a document to a markdown format.
    """
    document_converter: DoclingDocumentConverter = app.state.converter
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        try:
            result = await loop.run_in_executor(
                pool, 
                document_converter.convert, 
                *[request.document_name, request.chunk_size],
            )
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

    return result


    