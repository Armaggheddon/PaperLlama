from dataclasses import dataclass

@dataclass
class Metadata:
    faiss_id: int
    user_filename: str
    subindex_filename: str
    pdffile_path: str
    document_hash: str
    document_summary: str

@dataclass
class BaseMetadata:
    faiss_id: int
    subindex_filename: str
    summary: str