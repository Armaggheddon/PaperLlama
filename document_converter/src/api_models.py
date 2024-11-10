from pydantic import BaseModel
from typing import Optional

class ConvertDocumentRequest(BaseModel):
    document_name: str
    chunk_size: Optional[int] = 800

class ConvertDocumentResponse(BaseModel):
    text_chunks: list[str]