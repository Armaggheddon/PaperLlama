import os
import pathlib

import faiss

from . import utils

_INDEX_EXTENSION = "index"

class VectorDB:
    def __init__(
        self, 
        embedding_length: int, 
        data_root: str, 
        root_index_name: str, 
        sub_index_path: str
    ) -> None:
        self.embedding_length = embedding_length
        self.root_index_path = pathlib.Path(data_root) / root_index_name
        
        if not os.path.isfile(str(self.root_index_path)):
            faiss.write_index(
                self._create_empty_index(), 
                str(self.root_index_path)
            )
        
        self.sub_index_path = sub_index_path

        self.root_index = faiss.read_index(str(self.root_index_path))

    def _create_empty_index(self):
        return faiss.IndexFlatL2(self.embedding_length)
    
    def _touch_index(self, index_path: str, ovwerwrite: bool=False):
        if not os.path.isfile(index_path):
            # index does not exist
            faiss.write_index(self._create_empty_index(), index_path)
        elif ovwerwrite:
            os.remove(index_path)
            faiss.write_index(self._create_empty_index(), index_path)
        return faiss.read_index(index_path)

    def get_root_offset_id(self):
        return self.root_index.ntotal-1

    def add_to_root(self, vectors: list[list[float]]):
        return self.root_index.add(utils.embeddings_to_numpy(vectors))

    def add(self, index_name: str, vectors: list[list[float]], ovwerwrite: bool=False):
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        tmp_index = self._touch_index(str(index_path), ovwerwrite)
        tmp_index.add(utils.embeddings_to_numpy(vectors))
        faiss.write_index(tmp_index, str(index_path))
    
    def get_index_offset_id(self, index_name: str):
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        tmp_index = self._touch_index(str(index_path))
        return tmp_index.ntotal-1

    def query_root(self, vector: list[float], top_k: int):
        D, I = self.root_index.search(utils.embeddings_to_numpy(vector), top_k)
        return D, I

    def query(self, index_path: str, vector: list[float], top_k: int):
        if not os.path.isfile(index_path):
            raise ValueError(f"Index {index_path} does not exist")

        tmp_index = faiss.read_index(index_path)
        D, I = tmp_index.search(utils.embeddings_to_numpy(vector), top_k)
        tmp_index.close()
        return D, I


