from pydantic import BaseModel

class DocumentChunk(BaseModel):
    text: str
    page_number: int

class RootQueryResult(BaseModel):
    uuid: str
    summary: str

class RootQueryRequest(BaseModel):
    query_embedding: list[float]

class DocumentQueryRequest(BaseModel):
    document_uuids: list[str]
    query_embedding: list[float]

class AddDocumentChunk(BaseModel):
    text: str
    page_number: int
    embedding: list[float]

class AddDocumentRequest(BaseModel):
    document_uuid: str
    document_hash_str: str
    document_filename: str
    document_embedding: list[float]
    document_summary: str
    document_chunks: list[AddDocumentChunk]

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