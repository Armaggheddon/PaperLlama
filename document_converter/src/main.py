import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, status

from converter import DoclingDocumentConverter

import api_models


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.converter = DoclingDocumentConverter()

    yield

    # close, or wait termination?


app = FastAPI(
    lifespan=lifespan
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/convert_document", response_model=api_models.ConvertDocumentResponse)
async def convert_document(request: api_models.ConvertDocumentRequest):
    
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


    