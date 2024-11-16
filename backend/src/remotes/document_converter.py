from pydantic import BaseModel

DOCUMENT_CONVERTER_BASE_URL = "http://document_converter:8000"
CONVERT_DOCUMENT_URL = f"{DOCUMENT_CONVERTER_BASE_URL}/convert_document"

HEALTH_URL = f"{DOCUMENT_CONVERTER_BASE_URL}/health"

class ConvertDocumentRequest(BaseModel):
    document_name: str

class ConvertDocumentResponse(BaseModel):
    text_chunks: list[str]

class HealthCheckResponse(BaseModel):
    up_time: float
    status: str