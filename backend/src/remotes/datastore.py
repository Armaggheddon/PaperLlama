from pydantic import BaseModel


DATASTORE_BASE_URL = "http://datastore:8000"
HAS_DOCUMENT_URL = f"{DATASTORE_BASE_URL}/has_document"
HAS_DOCUMENT_UUID = f"{DATASTORE_BASE_URL}/has_document_uuid"
ADD_DOCUMENT_URL = f"{DATASTORE_BASE_URL}/add_document"
DELETE_ALL_DOCUMENTS_URL = f"{DATASTORE_BASE_URL}/delete_all"
DELETE_DOCUMENT_URL = f"{DATASTORE_BASE_URL}/delete_document"
DOCUMENTS_INFO_URL = f"{DATASTORE_BASE_URL}/documents_info"
QUERY_ROOT_URL = f"{DATASTORE_BASE_URL}/query_root"
QUERY_DOCUMENT_URL = f"{DATASTORE_BASE_URL}/query_document"

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