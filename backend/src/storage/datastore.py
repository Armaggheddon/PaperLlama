import os
from re import sub
from urllib.parse import quote_from_bytes
import uuid
import shutil
from typing import Callable
import asyncio

from .vector_db import VectorDB
from .metadata_db import MetadataDB, BaseMetadata

from . import utils

DATA_ROOT = "/vector_index"
ROOT_INDEX_NAME = "root_index"
ROOT_DB_NAME = "root_metadata"
SUB_INDEX_PATH = "/vector_index/sub_indexes"
FILES_PATH = "/vector_index/files"

_vector_db_config = {
    "data_root": DATA_ROOT,
    "root_index_name": ROOT_INDEX_NAME,
    "sub_index_path": SUB_INDEX_PATH,
}

_metadata_db_config = {
    "data_root": DATA_ROOT,
    "root_db_name": ROOT_DB_NAME,
    "sub_index_path": SUB_INDEX_PATH,
}

class DataStore:
    def __init__(self, embedding_length: int) -> None:

        if not os.path.isdir(DATA_ROOT):
            # data root must exist since is persistent!!
            raise RuntimeError("Data root does not exist!!")
        if not os.path.isdir(SUB_INDEX_PATH):
            os.makedirs(SUB_INDEX_PATH)
        
        if not os.path.isdir(FILES_PATH):
            os.makedirs(FILES_PATH)
        
        self.vector_db = VectorDB(
            embedding_length=embedding_length,
            **_vector_db_config
        )

        self.metadata_db = MetadataDB(
            **_metadata_db_config
        )

    def has_document(self, file_bytes: bytes):
        file_hash = utils.hash_file(file_bytes)
        return self.metadata_db.has_document(file_hash)

    def add_document(
        self, 
        file_name: str,
        file_bytes: bytes,
        summary_embedding: list[float],
        summary_text: str,
        embeddings: list[list[float]], 
        text_chunks: list[str],
        overwrite: bool=False
    ):
        # query sqlite if file with same hash exists
        # if not, add to metadata db
        # add to vector db
        # add to sub index
        # add to sub index metadata db
        file_hash = utils.hash_file(file_bytes)
        
        # save the file
        base_file_name = str(uuid.uuid4())
        file_path = os.path.join(FILES_PATH, f"{base_file_name}.pdf")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # add the document to the root
        root_id = self.vector_db.add_to_root(vectors=summary_embedding)

        self.metadata_db.add_document_to_root(
            faiss_id=root_id,
            user_filename=file_name,
            subindex_filename=base_file_name,
            pdf_file_path=file_path,
            document_hash=file_hash,
            document_summary=summary_text
        )

        subindex_ids = self.vector_db.add(
            index_name=base_file_name,
            vectors=embeddings,
            ovwerwrite=overwrite
        )

        self.metadata_db.add_document(
            subindex_filename=base_file_name,
            pages=[i for i in range(len(text_chunks))],
            faiss_ids=subindex_ids,
            text_chunks=text_chunks
        )

    def query(
        self,
        query_embedding: list[float], 
        top_k_files: int=3, 
        top_k_chunks: int=5
    ):
        
        root_ids = self.vector_db.query_root(query_embedding, top_k_files)
        subindex_names: list[str] = self.metadata_db.get_documents_for_ids(root_ids)

        print(f"Root ids: {root_ids}")
        print(f"File names: {subindex_names}")

        chunk_texts = []
        for subindex_name in subindex_names:
            sub_index_chunks_ids = self.vector_db.query(subindex_name, query_embedding, top_k_chunks)
            sub_index_text_chunks: list[str] = self.metadata_db.get_document_chunks_for_ids(subindex_name, sub_index_chunks_ids)
            
            chunk_texts.extend(sub_index_text_chunks)
        return chunk_texts

    def get_all_documents(self):
        # get all the document names from the root metadata db
        return self.metadata_db.get_all_documents()
    
    def get_document_count(self):
        return self.metadata_db.get_document_count()
        

    def delete_document_by_ids(self, document_ids: list[int]):
        subindex_filenames = self.metadata_db.get_documents_for_ids(document_ids)
        for subindex_filename in subindex_filenames:
            self.vector_db.delete(subindex_filename)
            self.metadata_db.delete(subindex_filename)
            os.remove(os.path.join(FILES_PATH, f"{subindex_filename}.pdf"))
        
        self.vector_db.remove_from_root(document_ids)
        self.metadata_db.remove_document_from_root(document_ids)

    def delete_all(self):
        self.vector_db.clear_root()
        self.metadata_db.clear_root()

        shutil.rmtree(SUB_INDEX_PATH)
        shutil.rmtree(FILES_PATH)

        os.makedirs(SUB_INDEX_PATH)
        os.makedirs(FILES_PATH)
        

    def close(self):
        self.vector_db.close()
        self.metadata_db.close()