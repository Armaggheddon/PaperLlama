from embedding import OllamaEmbed

from .vector_db import VectorDB
from .metadata_db import MetadataDB


from parser import pdf_parse

DATA_ROOT = "/vector_index/data"
ROOT_INDEX_NAME = "root.index"
ROOT_DB_NAME = "root.db"
SUB_INDEX_PATH = "/vector_index/data/sub_indexes"
FILES_PATH = "/vector_index/data/files"

_vector_db_config = {
    "data_root": DATA_ROOT,
    "root_index_name": ROOT_INDEX_NAME,
    "sub_index_path": SUB_INDEX_PATH,
}

_metadata_db_config = {
    "data_root": DATA_ROOT,
    "root_db_name": ROOT_DB_NAME
}

class StorageManager:
    def __init__(self, embedding_length: int) -> None:
        
        self.vector_db = VectorDB(
            embedding_length=embedding_length,
            **_vector_db_config
        )

        self.metadata_db = MetadataDB(
            **_metadata_db_config
        )

    def add_document(self, file: str | bytes):
        # get the pages
        # get the embeddings
        # add the embeddings to the vector db
        # add the metadata to the metadata db
        # add the file to the files db
        text_chunks: list[str] = pdf_parse.to_chunks(file)
        


    def query(self, query: str | bytes):
        # get the embeddings
        # query the vector db
        # get the metadata
        # return the relevant chunks
        pass