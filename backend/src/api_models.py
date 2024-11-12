from typing import Optional
from pydantic import BaseModel

class DeleteIndexIdsRequest(BaseModel):
    index_ids: list[int]

class DeleteAllRequest(BaseModel):
    confirm: bool

class UploadFileResponse(BaseModel):
    is_success: bool
    message: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    text: str
    history: list[ChatMessage]

class QueryDocumentRequest(BaseModel):
    document_uuid: str
    query_str: str
    history: list[ChatMessage]