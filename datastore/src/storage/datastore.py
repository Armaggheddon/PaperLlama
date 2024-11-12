import os
import hashlib
import uuid
import shutil

from .metadata import MetadataDB
from .index import VectorIndex

from api_models import AddDocumentChunk, RootQueryResult, DocumentInfoResponse, DocumentChunk


_DATA_ROOT = "/vector_index"
_ROOT_INDEX_NAME = "root_index"
_ROOT_METADATA_NAME = "root_medatata"
_SUB_INDEX_PATH = "/vector_index/sub_index"
_UPLOADED_FILES_PATH = "/uploaded_files"

_vector_db_config = {
    "data_root": _DATA_ROOT,
    "root_index_name": _ROOT_INDEX_NAME,
    "sub_index_path": _SUB_INDEX_PATH 
}

_metadata_db_config = {
    "data_root": _DATA_ROOT,
    "root_db_name": _ROOT_METADATA_NAME,
    "sub_index_path": _SUB_INDEX_PATH
}

class DataStore:
    def __init__(self, embedding_length) -> None:

        if not os.path.isdir(_DATA_ROOT):
            raise RuntimeError(f"Data root at {_DATA_ROOT} does not exist!")
        if not os.path.isdir(_UPLOADED_FILES_PATH):
            raise RuntimeError(
                f"Uploaded files path at {_UPLOADED_FILES_PATH} does not exist!")

        if not os.path.isdir(_SUB_INDEX_PATH):
            os.makedirs(_SUB_INDEX_PATH)
        self.embedding_length = embedding_length
        self.vector_index = VectorIndex(embedding_length, **_vector_db_config)
        self.metadata_db = MetadataDB(**_metadata_db_config) 

    def has_document(
        self,
        document_hash_str: str
    ) -> bool:
        return self.metadata_db.has_document(document_hash_str)
    
    def has_document_uuid(
        self,
        document_uuid: str
    ) -> bool:
        return self.metadata_db.has_document_uuid(document_uuid)

    def add_document(
        self,
        document_uuid: str,
        document_hash_str: str,
        document_filename: str,
        document_embedding: list[float],
        document_summary: str,
        document_chunks: list[AddDocumentChunk]
    ):
        """ Add a document to the datastore. 
        Internally manages adding the document to both the 
        metadata and vector databases.
        """
        if self.metadata_db.has_document(document_hash_str):
            raise ValueError("Document already exists in the datastore!")
        
        root_index_id = self.vector_index.add_to_root(document_embedding)
        self.metadata_db.add_root_metadata(
            root_index_id,
            document_uuid,
            document_hash_str,
            document_filename,
            document_summary
        )

        chunks_embeddings = [
            chunk.embedding for chunk in document_chunks
        ]
        # print(chunks_embeddings, len(chunks_embeddings))
        sub_index_ids = self.vector_index.add(
            document_uuid,
            chunks_embeddings
        )

        chunks_text = [
            chunk.text for chunk in document_chunks
        ]
        chunks_page = [
            chunk.page_number for chunk in document_chunks
        ]

        self.metadata_db.add(
            document_uuid,
            sub_index_ids,
            chunks_page,
            chunks_text
        )   
    
    def delete_document(
        self,
        document_uuid: str
    ) -> str:
        
        faiss_id, document_filename = self.metadata_db.remove_from_root(document_uuid)
        self.vector_index.remove_from_root(faiss_id)
        self.metadata_db.remove(document_uuid)
        self.vector_index.remove(document_uuid)

        return document_filename
        

    def query_root(
        self,
        query_embedding: list[float]
    ) -> list[RootQueryResult]:
        root_ids = self.vector_index.query_root(query_embedding)
        query_result = self.metadata_db.query_root(root_ids)
        result = [
            RootQueryResult(uuid=row[0], summary=row[1])
            for row in query_result
        ]
        return result
    
    def query_documents(
        self,
        document_uuids: str | list[str],
        query_embedding: list[float]
    ) -> list[DocumentChunk]:
        
        if isinstance(document_uuids, str):
            document_uuids = [document_uuids]
        
        result = []
        for document_uuid in document_uuids:
            faiss_ids = self.vector_index.query(document_uuid, query_embedding)
            query_result = self.metadata_db.query(document_uuid, faiss_ids)
            # print(query_result, faiss_ids)
            result.extend([
                DocumentChunk(text=row[1], page_number=row[0])
                for row in query_result
            ])
            
        return result
    
    def get_documents_info(self) -> DocumentInfoResponse:
        documents_info = self.metadata_db.get_documents_info()
        return DocumentInfoResponse(
            document_count=len(documents_info),
            documents_info=documents_info
        )

        
    def close(self):
        self.vector_index.close()
        self.metadata_db.close()

    def clear(self):
        self.vector_index.clear_root()
        self.metadata_db.clear_root()

        shutil.rmtree(_SUB_INDEX_PATH)
        os.makedirs(_SUB_INDEX_PATH)
    