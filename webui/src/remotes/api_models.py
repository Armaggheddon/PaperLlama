from pydantic import BaseModel
from typing import Optional


class DocumentInfo(BaseModel):
    document_uuid: str
    document_hash_str: str
    document_filename: str
    document_summary: str

class DocumentInfoResponse(BaseModel):
    document_count: int
    documents_info: list[DocumentInfo]

class HasDocumentResponse(BaseModel):
    has_document: bool

class UploadFileResponse(BaseModel):
    is_success: bool
    message: Optional[str] = None