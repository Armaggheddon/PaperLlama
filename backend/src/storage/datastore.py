# from embedding import OllamaEmbed
from ctypes import util
import os
import hashlib
from re import sub
import uuid

from .vector_db import VectorDB
from .metadata_db import MetadataDB

from . import utils

DATA_ROOT = "/vector_index"
ROOT_INDEX_NAME = "root.index"
ROOT_DB_NAME = "root.db"
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
        has_file = self.metadata_db.has_document(file_hash)

        if has_file and not overwrite:
            raise RuntimeError("File already exists in the database!!")
        
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
        # get the embeddings
        # query the vector db
        # get the metadata
        # return the relevant chunks
        pass

    def get_document_names(self):
        # get all the document names from the root metadata db
        pass

    def delete_document(self, document_name: str):
        # delete the document from the root metadata db
        # delete the document from the vector db
        # delete the document from the sub index
        # delete the document from the sub index metadata db
        pass

    def close(self):
        self.vector_db.close()
        self.metadata_db.close()